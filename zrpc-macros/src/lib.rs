/*********************************************************************************
* Copyright (c) 2018,2020 ADLINK Technology Inc.
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
* which is available at https://www.apache.org/licenses/LICENSE-2.0.
*
* SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
* Contributors:
*   ADLINK fog05 team, <fog05@adlink-labs.tech>
*********************************************************************************/

#![recursion_limit = "512"]

extern crate base64;
extern crate darling;
extern crate proc_macro;
extern crate proc_macro2;
extern crate quote;
extern crate serde;
extern crate syn;

use darling::FromMeta;
use inflector::cases::snakecase::to_snake_case;
use proc_macro::TokenStream;
use proc_macro2::{Span, TokenStream as TokenStream2};
use quote::{format_ident, quote, ToTokens};
use std::str::FromStr;
use syn::{
    braced,
    ext::IdentExt,
    parenthesized,
    parse::{Parse, ParseStream},
    parse_macro_input, parse_quote,
    spanned::Spanned,
    token::Comma,
    Attribute, AttributeArgs, Block, FnArg, Ident, ImplItem, ImplItemMethod, ImplItemType,
    ItemImpl, Pat, PatType, Receiver, ReturnType, Token, Type, Visibility,
};
use uuid::Uuid;

macro_rules! extend_errors {
    ($errors: ident, $e: expr) => {
        match $errors {
            Ok(_) => $errors = Err($e),
            Err(ref mut errors) => errors.extend($e),
        }
    };
}

#[derive(Debug, FromMeta)]
struct ZServiceMacroArgs {
    timeout_s: u16,
    #[darling(default)]
    prefix: Option<String>,
    #[darling(default)]
    service_uuid: Option<String>,
}

struct ZService {
    attrs: Vec<Attribute>,
    vis: Visibility,
    ident: Ident,
    evals: Vec<EvalMethod>,
}

impl Parse for ZService {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let attrs = input.call(Attribute::parse_outer)?;
        let vis = input.parse()?;
        input.parse::<Token![trait]>()?;
        let ident: Ident = input.parse()?;
        let content;
        braced!(content in input);
        let mut evals = Vec::<EvalMethod>::new();
        while !content.is_empty() {
            evals.push(content.parse()?);
        }
        let mut ident_errors = Ok(());
        for eval in &evals {
            if eval.ident == "new" {
                extend_errors!(
                    ident_errors,
                    syn::Error::new(
                        eval.ident.span(),
                        format!(
                            "method name conflicts with generated fn `{}Client::new`",
                            ident.unraw()
                        )
                    )
                );
            }
            if eval.ident == "serve" {
                extend_errors!(
                    ident_errors,
                    syn::Error::new(
                        eval.ident.span(),
                        format!("method name conflicts with generated fn `{}::serve`", ident)
                    )
                );
            }
        }
        ident_errors?;

        Ok(Self {
            attrs,
            vis,
            ident,
            evals,
        })
    }
}

struct EvalMethod {
    attrs: Vec<Attribute>,
    ident: Ident,
    nochk: Ident,
    receiver: Receiver,
    args: Vec<PatType>,
    output: ReturnType,
}

impl Parse for EvalMethod {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let attrs = input.call(Attribute::parse_outer)?;
        input.parse::<Token![async]>()?;
        input.parse::<Token![fn]>()?;
        let ident = input.parse()?;
        let nochk = format_ident!("{}_nochk", ident);
        let content;
        let mut recv: Option<Receiver> = None;
        parenthesized!(content in input);
        let mut args = Vec::new();
        let mut errors = Ok(());
        for arg in content.parse_terminated::<FnArg, Comma>(FnArg::parse)? {
            match arg {
                FnArg::Typed(captured) if matches!(&*captured.pat, Pat::Ident(_)) => {
                    args.push(captured);
                }
                FnArg::Typed(captured) => {
                    extend_errors!(
                        errors,
                        syn::Error::new(captured.pat.span(), "patterns aren't allowed in RPC args")
                    );
                }
                FnArg::Receiver(receiver) => {
                    //Should take whatever used by the user and strip it for client
                    recv = Some(receiver)
                    // extend_errors!(
                    //     errors,
                    //     syn::Error::new(arg.span(), "method args cannot start with self, &mut self is added by the macro!")
                    // );
                }
            }
        }
        match recv {
            None => extend_errors!(
                errors,
                syn::Error::new(
                    recv.span(),
                    "Missing any receiver in method declaration, please add one!"
                )
            ),
            Some(_) => (),
        }

        errors?;
        let output = input.parse()?;
        input.parse::<Token![;]>()?;
        let receiver = recv.unwrap();

        Ok(Self {
            attrs,
            ident,
            nochk,
            receiver,
            args,
            output,
        })
    }
}

/// Generates:
/// - service trait
/// - serve fn
/// - client stub struct
/// - new_stub client factory fn
/// - Request and Response enums
#[proc_macro_attribute]
pub fn zservice(_attr: TokenStream, input: TokenStream) -> TokenStream {
    let unit_type: &Type = &parse_quote!(());

    //parsing the trait body
    let ZService {
        ref attrs,
        ref vis,
        ref ident,
        ref evals,
    } = parse_macro_input!(input as ZService);

    //parsing the attributes to the macro
    let attr_args = parse_macro_input!(_attr as AttributeArgs);
    let macro_args = match ZServiceMacroArgs::from_list(&attr_args) {
        Ok(v) => v,
        Err(e) => {
            return TokenStream::from(e.write_errors());
        }
    };

    //converts the functions names from snake_case to CamelCase
    let camel_case_fn_names: &Vec<_> = &evals
        .iter()
        .map(|eval| snake_to_camel(&eval.ident.unraw().to_string()))
        .collect();

    let snake_case_ident = to_snake_case(&ident.unraw().to_string());

    // Collects the pattern for the types
    let args: &[&[PatType]] = &evals.iter().map(|eval| &*eval.args).collect::<Vec<_>>();

    let service_uuid = match macro_args.service_uuid {
        Some(u) => Uuid::from_str(&u).unwrap(),
        None => Uuid::new_v4(),
    };

    //service eval path
    let path = match macro_args.prefix {
        Some(prefix) => format!("{}/zservice/{}/{}/", prefix, ident, service_uuid),
        None => format!("/zservice/{}/{}/", ident, service_uuid),
    };

    let service_name = format!("{}Service", ident);
    // Generates the code
    let ts: TokenStream = ZServiceGenerator {
        service_ident: ident,
        server_ident: &format_ident!("Serve{}", ident), //Server is called Serve<Trait Name>
        client_ident: &format_ident!("{}Client", ident), //Client is called <Trait Name>Client
        request_ident: &format_ident!("{}Request", ident), //Request type is called <Trait Name>Request
        response_ident: &format_ident!("{}Response", ident), //Response type is called <Trait Name>Response
        vis,
        args,
        method_attrs: &evals.iter().map(|eval| &*eval.attrs).collect::<Vec<_>>(), //getting evals attributes
        method_idents: &evals.iter().map(|eval| &eval.ident).collect::<Vec<_>>(), //getting evals names
        method_idents_nocheck: &evals.iter().map(|eval| &eval.nochk).collect::<Vec<_>>(), //getting evals names no check [TESTING]
        attrs,
        evals,
        return_types: &evals //getting evals return type, if non present using unit
            .iter()
            .map(|eval| match eval.output {
                ReturnType::Type(_, ref ty) => ty,
                ReturnType::Default => unit_type,
            })
            .collect::<Vec<_>>(),
        arg_pats: &args
            .iter()
            .map(|args| args.iter().map(|arg| &*arg.pat).collect())
            .collect::<Vec<_>>(),
        camel_case_idents: &evals
            .iter()
            .zip(camel_case_fn_names.iter())
            .map(|(eval, name)| Ident::new(name, eval.ident.span()))
            .collect::<Vec<_>>(),
        timeout: &macro_args.timeout_s,
        eval_path: &path,
        service_name: &service_name,
        service_get_server_ident: &format_ident!("get_{}_server", snake_case_ident),
    }
    .into_token_stream()
    .into();
    ts
}

/// Update the implementation of the trait
#[proc_macro_attribute]
pub fn zserver(_attr: TokenStream, input: TokenStream) -> TokenStream {
    let mut item = syn::parse_macro_input!(input as ItemImpl);
    let span = item.span();

    // let attr_args = parse_macro_input!(_attr as AttributeArgs);

    let mut expected_non_async_types: Vec<(&ImplItemMethod, String)> = Vec::new();
    let mut found_non_async_types: Vec<&ImplItemType> = Vec::new();

    for inner in &mut item.items {
        match inner {
            ImplItem::Method(method) => {
                if method.sig.asyncness.is_some() {
                    // if this function is declared async, transform it into a regular function
                    method.sig.asyncness = None;
                    // put the body inside an task::block_on(async {})
                    let content = method.block.to_token_stream();
                    // and add the  #[allow(unused,clippy::manual_async_fn)] attribute
                    // let new_attr = TokenStream::from(quote!{
                    //     #[allow(unused,clippy::manual_async_fn)]
                    // });
                    // let attrs = new_attr.call(Attribute::parse_outer).unwrap();
                    // method.attrs.push(attrs);

                    let updated_impl = TokenStream::from(quote! {
                        {
                            task::block_on(
                                async move
                                #content
                            )
                        }
                    });
                    method.block = parse_macro_input!(updated_impl as Block);
                } else {
                    // If it's not async, keep track of all required associated types for better
                    // error reporting.
                    expected_non_async_types.push((method, associated_type_for_eval(method)));
                }
            }
            ImplItem::Type(typedecl) => found_non_async_types.push(typedecl),
            _ => {}
        }
    }

    if let Err(e) =
        verify_types_were_provided(span, &expected_non_async_types, &found_non_async_types)
    {
        return TokenStream::from(e.to_compile_error());
    }

    // let uuid = match macro_args.uuid {
    //     Some(u) => Uuid::from_str(&u).unwrap(),
    //     None => Uuid::new_v4(),
    // };

    // let str_uuid = format!("{}", uuid);

    // let uuid_imp = TokenStream::from(quote! {
    //     fn instance_uuid(&self) -> uuid::Uuid {
    //         Uuid::from_str(#str_uuid).unwrap()
    //     }
    // });

    // let method = syn::parse_macro_input!(uuid_imp as syn::ImplItemMethod);

    // item.items.push(ImplItem::Method(method));

    TokenStream::from(quote!(#item))
}

/// Creates the type name for a future, to be removed...
fn associated_type_for_eval(method: &ImplItemMethod) -> String {
    snake_to_camel(&method.sig.ident.unraw().to_string()) + "Fut"
}

/// Verifies if the types are provide for each methods
fn verify_types_were_provided(
    span: Span,
    expected: &[(&ImplItemMethod, String)],
    provided: &[&ImplItemType],
) -> syn::Result<()> {
    let mut result = Ok(());
    for (method, expected) in expected {
        if !provided.iter().any(|typedecl| typedecl.ident == expected) {
            let mut e = syn::Error::new(
                span,
                format!("not all trait items implemented, missing: `{}`", expected),
            );
            let fn_span = method.sig.fn_token.span();
            e.extend(syn::Error::new(
                fn_span.join(method.sig.ident.span()).unwrap_or(fn_span),
                format!(
                    "hint: `#[zerver]` only rewrites async fns, and `fn {}` is not async",
                    method.sig.ident
                ),
            ));
            match result {
                Ok(_) => result = Err(e),
                Err(ref mut error) => error.extend(Some(e)),
            }
        }
    }
    result
}

/// Generator for the ZService
struct ZServiceGenerator<'a> {
    service_ident: &'a Ident,               //service type
    server_ident: &'a Ident,                //server type
    client_ident: &'a Ident,                //client type
    request_ident: &'a Ident,               //request type
    response_ident: &'a Ident,              //response type
    vis: &'a Visibility,                    //visibility
    attrs: &'a [Attribute],                 //attributes
    evals: &'a [EvalMethod],                //functions to be exposed via evals
    camel_case_idents: &'a [Ident],         //camel case conversion of all names
    method_idents: &'a [&'a Ident],         //type of the methods
    method_idents_nocheck: &'a [&'a Ident], //type of the methods without check of the server [TESTING POURPOSE]
    method_attrs: &'a [&'a [Attribute]],    //attributes of the methods
    args: &'a [&'a [PatType]],              // types description pattern
    return_types: &'a [&'a Type],           // return types of functions
    arg_pats: &'a [Vec<&'a Pat>],           // patterns for args
    timeout: &'a u16,                       //eval timeout
    eval_path: &'a String,                  //path for evals
    service_name: &'a String,               //service name on zenoh
    service_get_server_ident: &'a Ident,    //the ident for the get_<trait>_server
}

impl<'a> ZServiceGenerator<'a> {
    // crates the service trait
    fn trait_service(&self) -> TokenStream2 {
        let &Self {
            attrs,
            evals,
            vis,
            return_types,
            service_ident,
            server_ident,
            service_get_server_ident,
            ..
        } = self;

        let fns = evals.iter().zip(return_types.iter()).map(
            |(
                EvalMethod {
                    attrs,
                    ident,
                    receiver,
                    args,
                    ..
                },
                output,
            )| {
                quote! {

                    #(#attrs)*
                    fn #ident(#receiver, #(#args),*) -> #output;
                }
            },
        );

        quote! {
        #(#attrs)*
        #vis trait #service_ident : Clone{
            #(#fns)*

            /// Returns the server object
            fn #service_get_server_ident(self, z : async_std::sync::Arc<zenoh::Zenoh>, id : Option<uuid::Uuid>) -> #server_ident<Self>{
                let id = id.unwrap_or(Uuid::new_v4());
                log::trace!("Getting Server with ID {}", id);
                #server_ident::new(z,self, id)
                }
            }

        }
    }

    //creates the server struct
    fn struct_server(&self) -> TokenStream2 {
        let &Self {
            vis, server_ident, ..
        } = self;

        quote! {
            #[derive(Clone)]
            #vis struct #server_ident<S> {
                z : async_std::sync::Arc<zenoh::Zenoh>,
                server: S,
                instance_id: uuid::Uuid,
            }

            impl<S> #server_ident<S> {
                pub fn new(z : Arc<zenoh::Zenoh>, server : S, id : uuid::Uuid) -> Self {
                    Self {
                        z,
                        server,
                        instance_id : id,
                    }
                }
            }

        }
    }

    // implements ZServe for the server
    fn impl_serve_for_server(&self) -> TokenStream2 {
        let &Self {
            request_ident,
            server_ident,
            service_ident,
            response_ident,
            camel_case_idents,
            arg_pats,
            method_idents,
            eval_path,
            service_name,
            ..
        } = self;

        quote! {


            impl<S> zrpc::ZServe<#request_ident> for #server_ident<S>
            where S: #service_ident + Send +'static
            {
                type Resp = #response_ident;

                fn instance_uuid(&self) -> uuid::Uuid {
                    self.instance_id
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn connect(&'_ self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>>+ '_>> {
                    log::trace!("Connect Service {} Instance {}", #service_name, self.instance_uuid());

                    async fn __connect<S>(_self: &#server_ident<S>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                    {

                        let zsession = _self.z.session();
                        let zinfo = zsession.info().await;
                        let pid = zinfo.get(&zenoh::net::info::ZN_INFO_PID_KEY).ok_or(ZRPCError::MissingValue)?.to_uppercase();
                        let rid = zinfo.get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY).ok_or(ZRPCError::MissingValue)?.split(",").collect::<Vec<_>>()[0].to_uppercase();
                        let ws = _self.z.workspace(None).await?;


                        let component_info = zrpc::ComponentState{
                            uuid : _self.instance_uuid(),
                            name : format!("{}", #service_name),
                            routerid : rid.clone().to_uppercase(),
                            peerid : pid.clone().to_uppercase(),
                            status : zrpc::ComponentStatus::HALTED,
                        };
                        let encoded_ci = zrpc::serialize::serialize_state(&component_info)?;
                        let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;

                        ws.put(&path.into(),encoded_ci.into()).await?;

                        let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                        let max_retries = 10_000;
                        let mut i = 0;

                        loop {
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            if data.len() > 0 {
                                return Ok(())
                            }
                            if i >= max_retries {
                                return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                            }
                            i += 1;
                        }


                    }
                    Box::pin(__connect(self))
                }


                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn initialize(&self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
                    log::trace!("Initialize Service {} Instance {}", #service_name, self.instance_uuid());

                    fn check(data : &Vec<zenoh::Data>) -> ZRPCResult<bool> {
                        match data.len() {
                            0 => Ok(false),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        if ci.status == zrpc::ComponentStatus::INITIALIZING {
                                            return Ok(true);
                                        }
                                        Ok(false)
                                    },
                                    _ => Ok(false),
                                }
                            }
                            _ => Ok(false),
                        }
                    }

                    async fn __initialize<S>(_self: &#server_ident<S>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                    {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let ws = _self.z.workspace(None).await?;
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            match data.len() {
                                0 => Err(ZRPCError::NotFound),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                            match ci.status {
                                                zrpc::ComponentStatus::HALTED => {
                                                    ci.status = zrpc::ComponentStatus::INITIALIZING;
                                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    ws.put(&path,encoded_ci.into()).await?;

                                                    // This checks if the state is updated in zenoh
                                                    let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    let max_retries = 10_000;
                                                    let mut i = 0;

                                                    loop {
                                                        let ds = ws.get(&selector).await?;
                                                        let data : Vec<zenoh::Data> = ds.collect().await;
                                                        if check(&data)? {
                                                            return Ok(())
                                                        }
                                                        if i >= max_retries {
                                                            return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                                        }
                                                        i += 1;
                                                    }


                                                },
                                                _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot initialize a component in a state different than HALTED".to_string())),
                                            }
                                        },
                                        _ => Err(ZRPCError::ZenohError(
                                            "Component state is expected to be RAW in Zenoh!!".to_string()
                                        )),
                                    }
                                },
                                _ => Err(ZRPCError::Unreachable),
                            }
                    }
                    Box::pin(__initialize(self))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn register(&self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>{
                    log::trace!("Register Service {} Instance {}", #service_name, self.instance_uuid());

                    fn check(data : &Vec<zenoh::Data>) -> ZRPCResult<bool> {
                        match data.len() {
                            0 => Ok(false),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        if ci.status == zrpc::ComponentStatus::REGISTERED {
                                            return Ok(true);
                                        }
                                        Ok(false)
                                    },
                                    _ => Ok(false),
                                }
                            }
                            _ => Ok(false),
                        }
                    }


                    async fn __register<S>(_self: &#server_ident<S>) -> ZRPCResult<()>
                    where
                    S: #service_ident + Send + 'static,
                    {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let ws = _self.z.workspace(None).await?;
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            match data.len() {
                                0 => Err(ZRPCError::NotFound),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                            match ci.status {
                                                zrpc::ComponentStatus::INITIALIZING => {
                                                    ci.status = zrpc::ComponentStatus::REGISTERED;
                                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    ws.put(&path,encoded_ci.into()).await?;


                                                    // This checks if the state is updated in zenoh
                                                    let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    let max_retries = 10_000;
                                                    let mut i = 0;
                                                    loop {
                                                        let ds = ws.get(&selector).await?;
                                                        let data : Vec<zenoh::Data> = ds.collect().await;
                                                        if check(&data)? {
                                                            return Ok(())
                                                        }
                                                        if i >= max_retries {
                                                            return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                                        }
                                                        i += 1;
                                                    }
                                                },
                                                _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot register a component in a state different than INITIALIZING".to_string())),
                                            }
                                        },
                                        _ => Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                                    }
                                },
                                _ => Err(ZRPCError::Unreachable),
                            }
                        }
                    Box::pin(__register(self))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn start(
                    &self,
                ) -> ::core::pin::Pin<
                    Box<
                        dyn std::future::Future<
                                Output = ZRPCResult<(async_std::channel::Sender<()>, async_std::task::JoinHandle<ZRPCResult<()>>)>,
                            > + '_,
                    >,
                > {
                    log::trace!("Start Service {} Instance {}", #service_name, self.instance_uuid());

                    fn check(data : &Vec<zenoh::Data>) -> ZRPCResult<bool> {
                        match data.len() {
                            0 => Ok(false),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        if ci.status == zrpc::ComponentStatus::SERVING {
                                            return Ok(true);
                                        }
                                        Ok(false)
                                    },
                                    _ => Ok(false),
                                }
                            }
                            _ => Ok(false),
                        }
                    }


                    async fn __start<S>(
                        _self: &#server_ident<S>,
                    ) -> ZRPCResult<(async_std::channel::Sender<()>, async_std::task::JoinHandle<ZRPCResult<()>>)>
                    where
                        S: #service_ident + Send + 'static,
                    {
                            let (s, r) = async_std::channel::bounded::<()>(1);
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let ws = _self.z.workspace(None).await?;
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            match data.len() {
                                0 => Err(ZRPCError::NotFound),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                            match ci.status {
                                                zrpc::ComponentStatus::REGISTERED => {
                                                    ci.status = zrpc::ComponentStatus::SERVING;
                                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    ws.put(&path.into(),encoded_ci.into()).await?;

                                                    // This checks if the state is updated in zenoh
                                                    let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    let max_retries = 10_000;
                                                    let mut i = 0;

                                                    loop {
                                                        let ds = ws.get(&selector).await?;
                                                        let data : Vec<zenoh::Data> = ds.collect().await;
                                                        if check(&data)? {
                                                            break
                                                        }
                                                        if i >= max_retries {
                                                            return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                                        }
                                                        i += 1;
                                                    }


                                                    let server = _self.clone();
                                                    let h = async_std::task::spawn_blocking(move || {
                                                        async_std::task::block_on(async {
                                                            server.serve(r).await
                                                        })
                                                    });
                                                    Ok((s,h))
                                                },
                                                _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot start a component in a state different than REGISTERED".to_string())),
                                            }
                                        },
                                        _ => Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                                    }
                                },
                                _ => Err(ZRPCError::Unreachable),
                            }
                    }
                    Box::pin(__start(self))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn serve(
                    &self,
                    stop: async_std::channel::Receiver<()>,
                ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
                    log::trace!("Serve Service {} Instance {}", #service_name, self.instance_uuid());
                    async fn __serve<S>(_self: &#server_ident<S>, _stop: async_std::channel::Receiver<()>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                    {
                        let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                        let ws = _self.z.workspace(None).await?;
                        let ds = ws.get(&selector).await?;
                        let data : Vec<zenoh::Data> = ds.collect().await;
                        match data.len() {
                            0 => Err(ZRPCError::NotFound),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        match ci.status {
                                            zrpc::ComponentStatus::SERVING => {
                                                let path = zenoh::Path::try_from(format!("{}/{}/eval",#eval_path, _self.instance_uuid()))?;
                                                log::trace!("Registering eval on {:?}", path);
                                                let mut rcv = ws.register_eval(&path.clone().into()).await?;
                                                log::trace!("Registered on {:?}", path);
                                                let rcv_loop = async {
                                                    loop {
                                                        let get_request = rcv.next().await.ok_or_else(|| async_std::channel::RecvError)?;
                                                        let base64_req = get_request.selector.properties.get("req").cloned().ok_or_else(|| async_std::channel::RecvError)?;
                                                        let b64_bytes = base64::decode(base64_req).map_err(|_| async_std::channel::RecvError)?;
                                                        let req = zrpc::serialize::deserialize_request::<#request_ident>(&b64_bytes).map_err(|_| async_std::channel::RecvError)?;
                                                        log::trace!("Received on {:?} {:?}", path, req);

                                                        let mut ser = _self.server.clone();
                                                        let gr = get_request.clone();
                                                        let p = path.clone();
                                                        //log::trace!("Spawning task to respond to {:?}", req);

                                                        match req.clone() {
                                                            #(
                                                                #request_ident::#camel_case_idents{#(#arg_pats),*} => {
                                                                    let resp = #response_ident::#camel_case_idents(ser.#method_idents( #(#arg_pats),*));
                                                                    log::trace!("Reply to {:?} {:?} with {:?}", path, req, resp);
                                                                    let encoded =  zrpc::serialize::serialize_response(&resp).map_err(|_| async_std::channel::RecvError)?;
                                                                    gr.reply(p, encoded.into()).await;
                                                                    log::trace!("Response {:?} sent", resp);
                                                                }
                                                            )*
                                                        }
                                                    }
                                                };
                                                Ok(rcv_loop.race(_stop.recv()).await.map_err(|e| ZRPCError::Error(format!("{}", e)))?)
                                            },
                                            _ => Err(ZRPCError::StateTransitionNotAllowed("State is not WORK, serve called directly? serve is called by calling work!".to_string())),
                                        }
                                    },
                                    _ => Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                                }
                            },
                            _ => Err(ZRPCError::Unreachable),
                        }
                    }
                    Box::pin(__serve(self, stop))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn stop(
                    &self,
                    stop: async_std::channel::Sender<()>,
                ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
                    log::trace!("Stop Service {} Instance {}", #service_name, self.instance_uuid());

                    fn check(data : &Vec<zenoh::Data>) -> ZRPCResult<bool> {
                        match data.len() {
                            0 => Ok(false),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        if ci.status == zrpc::ComponentStatus::REGISTERED {
                                            return Ok(true);
                                        }
                                        Ok(false)
                                    },
                                    _ => Ok(false),
                                }
                            }
                            _ => Ok(false),
                        }
                    }

                    async fn __stop<S>(_self: &#server_ident<S>, _stop: async_std::channel::Sender<()>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                    {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let ws = _self.z.workspace(None).await?;
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            match data.len() {
                                0 => Err(ZRPCError::NotFound),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                            match ci.status {
                                                zrpc::ComponentStatus::SERVING => {
                                                    ci.status = zrpc::ComponentStatus::REGISTERED;
                                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    ws.put(&path.into(),encoded_ci.into()).await?;

                                                    // This checks if the state is updated in zenoh
                                                    let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    let max_retries = 10_000;
                                                    let mut i = 0;
                                                    loop {
                                                        let ds = ws.get(&selector).await?;
                                                        let data : Vec<zenoh::Data> = ds.collect().await;
                                                        if check(&data)? {
                                                            break
                                                        }
                                                        if i >= max_retries {
                                                            return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                                        }
                                                        i += 1;
                                                    }

                                                    Ok(_stop.send(()).await?)
                                                },
                                                _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot stop a component in a state different than WORK".to_string())),
                                            }
                                        },
                                        _ => Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                                    }
                                },
                                _ => Err(ZRPCError::Unreachable),
                            }
                        }
                    Box::pin(__stop(self, stop))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn unregister(&self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
                    log::trace!("Unregister Service {} Instance {}", #service_name, self.instance_uuid());

                    fn check(data : &Vec<zenoh::Data>) -> ZRPCResult<bool> {
                        match data.len() {
                            0 => Ok(false),
                            1 => {
                                let kv = &data[0];
                                match &kv.value {
                                    zenoh::Value::Raw(_,buf) => {
                                        let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                        if ci.status == zrpc::ComponentStatus::HALTED {
                                            return Ok(true);
                                        }
                                        Ok(false)
                                    },
                                    _ => Ok(false),
                                }
                            }
                            _ => Ok(false),
                        }
                    }

                    async fn __unregister<S>(_self: &#server_ident<S>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                    {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let ws = _self.z.workspace(None).await?;
                            let ds = ws.get(&selector).await?;
                            let data : Vec<zenoh::Data> = ds.collect().await;
                            match data.len() {
                                0 => Err(ZRPCError::NotFound),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                            match ci.status {
                                                zrpc::ComponentStatus::REGISTERED => {
                                                    ci.status = zrpc::ComponentStatus::HALTED;
                                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    ws.put(&path.into(),encoded_ci.into()).await?;


                                                    // This checks if the state is updated in zenoh
                                                    let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                                                    let max_retries = 10_000;
                                                    let mut i = 0;
                                                    loop {
                                                        let ds = ws.get(&selector).await?;
                                                        let data : Vec<zenoh::Data> = ds.collect().await;
                                                        if check(&data)? {
                                                            return Ok(())
                                                        }
                                                        if i >= max_retries {
                                                            return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                                        }
                                                        i += 1;
                                                    }

                                                },
                                                _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot unregister a component in a state different than REGISTERED".to_string())),
                                            }
                                        },
                                        _ => Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                                    }
                                },
                                _ => Err(ZRPCError::Unreachable),
                            }
                        }
                    Box::pin(__unregister(self))
                }

                #[allow(clippy::type_complexity,clippy::manual_async_fn)]
                fn disconnect(self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>>>> {
                    log::trace!("Disconnect Service {} Instance {}", #service_name, self.instance_uuid());
                    async fn __disconnect<S>(_self: #server_ident<S>) -> ZRPCResult<()>
                    where
                        S: #service_ident + Send + 'static,
                        {
                            let ws = _self.z.workspace(None).await?;
                            let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            ws.delete(&path).await?;


                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,_self.instance_uuid()))?;
                            let max_retries = 10_000;
                            let mut i = 0;

                            loop {
                                let ds = ws.get(&selector).await?;
                                let data : Vec<zenoh::Data> = ds.collect().await;
                                if data.len() == 0 {
                                    return Ok(())
                                }
                                if i >= max_retries {
                                    return Err(ZRPCError::ZenohError("Unable to check component state, did you miss a zenoh storage?".to_string()))
                                }
                                i += 1;
                            }

                        }
                    Box::pin(__disconnect(self))
                }

            }
        }
    }

    // Generates the request enum type, and makes it derive Debug, Serialize and Deserialize
    fn enum_request(&self) -> TokenStream2 {
        let &Self {
            vis,
            request_ident,
            camel_case_idents,
            args,
            ..
        } = self;

        quote! {
            /// The request sent over the wire from the client to the server.
            #[derive(Debug, serde::Serialize, serde::Deserialize, Clone)]
            #vis enum #request_ident {
                #( #camel_case_idents{ #( #args ),* } ),*
            }
        }
    }

    // Generates the response enum type, and makes it derive Debug, Serialize and Deserialize
    fn enum_response(&self) -> TokenStream2 {
        let &Self {
            vis,
            response_ident,
            camel_case_idents,
            return_types,
            ..
        } = self;

        quote! {
            /// The response sent over the wire from the server to the client.
            #[derive(Debug, serde::Serialize, serde::Deserialize, Clone)]
            #vis enum #response_ident {
                #( #camel_case_idents(#return_types) ),*
            }
        }
    }

    // Generates the client struct
    fn struct_client(&self) -> TokenStream2 {
        let &Self {
            vis,
            client_ident,
            request_ident,
            response_ident,
            ..
        } = self;

        quote! {
            #[allow(unused)]
            #[derive(Clone, Debug)]
            #vis struct #client_ident<C = zrpc::ZClientChannel<#request_ident, #response_ident>>{
                ch : C,
                server_uuid : Uuid,
            }
        }
    }

    // Generates the implentation of the client
    fn impl_client_new_find_servers(&self) -> TokenStream2 {
        let &Self {
            client_ident,
            vis,
            eval_path,
            ..
        } = self;

        quote! {
            impl #client_ident {
                #vis fn new(
                    z : async_std::sync::Arc<zenoh::Zenoh>,
                    instance_id : uuid::Uuid
                ) -> #client_ident {
                        let new_client = zrpc::ZClientChannel::new(z, format!("{}",#eval_path), Some(instance_id));
                        #client_ident{
                            ch : new_client,
                            server_uuid : instance_id,
                        }

                    }

                #vis fn get_server_uuid(&self) -> Uuid {
                    self.server_uuid
                }




                #vis fn find_local_servers(
                    z : async_std::sync::Arc<zenoh::Zenoh>
                ) -> impl std::future::Future<Output = ZRPCResult<Vec<uuid::Uuid>>> + 'static
                {
                    async move {
                        let ws = z.workspace(None).await?;
                        let zsession = z.session();
                        let zinfo = zsession.info().await;
                        let rid = zinfo.get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY).ok_or(ZRPCError::MissingValue)?.split(",").collect::<Vec<_>>()[0].to_uppercase();

                        let selector = zenoh::Selector::try_from(format!("{}/*/state",#eval_path))?;
                        let mut ds = ws.get(&selector).await?;
                        let mut servers = Vec::new();

                        while let Some(d) = ds.next().await {
                            match d.value {
                                zenoh::Value::Raw(_,buf) => {
                                    let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                    if ca.routerid == rid {
                                        servers.push(ca.uuid);
                                    }
                                },
                                _ => return Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string()))
                            }
                        }
                        Ok(servers)
                    }
                }


                #vis fn find_servers(
                    z : async_std::sync::Arc<zenoh::Zenoh>
                ) -> impl std::future::Future<Output = ZRPCResult<Vec<uuid::Uuid>>> + 'static
                {
                    async move {
                        let ws = z.workspace(None).await?;

                        let selector = zenoh::Selector::try_from(format!("{}/*/state",#eval_path))?;
                        let mut ds = ws.get(&selector).await?;
                        let mut servers = Vec::new();

                        while let Some(d) = ds.next().await {
                            match d.value {
                                zenoh::Value::Raw(_,buf) => {
                                    let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                                    servers.push(ca.uuid);
                                },
                                _ => return Err(ZRPCError::ZenohError("Component state is expected to be RAW in Zenoh!!".to_string())),
                            }
                        }
                        Ok(servers)
                    }
                    }



            }

        }
    }

    // Generates the implementation of the client methods that maps to evals
    fn impl_client_eval_methods(&self) -> TokenStream2 {
        let &Self {
            client_ident,
            request_ident,
            response_ident,
            method_attrs,
            vis,
            method_idents,
            method_idents_nocheck,
            args,
            return_types,
            arg_pats,
            camel_case_idents,
            timeout,
            ..
        } = self;

        quote! {
            impl #client_ident {


                #vis fn verify_server(&self
                ) -> impl std::future::Future<Output = ZRPCResult<bool>> + '_ {
                    async move {
                        self.ch.verify_server().await
                    }
                }

                #(
                    #[allow(unused,clippy::manual_async_fn)]
                    #( #method_attrs )*
                    #vis fn #method_idents(&self, #( #args ),*)
                        -> impl std::future::Future<Output = ZRPCResult<#return_types>> + '_ {
                        let request = #request_ident::#camel_case_idents { #( #arg_pats ),* };
                        log::trace!("Sending {:?}", request);
                        async move {
                            match self.ch.verify_server().await {
                                Ok(b) => {
                                    match b {
                                        false => Err(ZRPCError::Unavailable),
                                        true => {
                                            let resp = self.ch.call_fun(request);
                                            let dur = std::time::Duration::from_secs(#timeout as u64);
                                            match async_std::future::timeout(dur, resp).await {
                                                Ok(r) => match r {
                                                    Ok(zr) => match zr {
                                                            #response_ident::#camel_case_idents(msg) => std::result::Result::Ok(msg),
                                                            _ => Err(ZRPCError::Unreachable),
                                                        },
                                                    Err(e) => Err(e),
                                                },
                                                Err(e) => Err(ZRPCError::TimedOut),
                                            }
                                        }
                                    }
                                },
                                Err(e) => Err(e),
                            }
                        }
                    }

                    #[allow(unused,clippy::manual_async_fn)]
                    #( #method_attrs )*
                    #vis fn #method_idents_nocheck(&self, #( #args ),*)
                        -> impl std::future::Future<Output = ZRPCResult<#return_types>> + '_ {
                        let request = #request_ident::#camel_case_idents { #( #arg_pats ),* };
                        log::trace!("Sending {:?}", request);
                        async move {
                            let resp = self.ch.call_fun(request);
                            let dur = std::time::Duration::from_secs(#timeout as u64);
                            match async_std::future::timeout(dur, resp).await {
                                Ok(r) => match r {
                                    Ok(zr) => match zr {
                                            #response_ident::#camel_case_idents(msg) => std::result::Result::Ok(msg),
                                            _ => Err(ZRPCError::Unreachable),
                                        },
                                    Err(e) => Err(e),
                                },
                                Err(e) => Err(ZRPCError::TimedOut),
                            }
                        }
                    }
                )*
            }
        }
    }
}

//Converts ZServiceGenerator to actual code
impl<'a> ToTokens for ZServiceGenerator<'a> {
    fn to_tokens(&self, output: &mut TokenStream2) {
        output.extend(vec![
            self.trait_service(),
            self.struct_server(),
            self.impl_serve_for_server(),
            self.enum_request(),
            self.enum_response(),
            self.struct_client(),
            self.impl_client_new_find_servers(),
            self.impl_client_eval_methods(),
        ])
    }
}

//converts to snake_case to CamelCase, is used to convert functions name
fn snake_to_camel(ident_str: &str) -> String {
    let mut camel_ty = String::with_capacity(ident_str.len());

    let mut last_char_was_underscore = true;
    for c in ident_str.chars() {
        match c {
            '_' => last_char_was_underscore = true,
            c if last_char_was_underscore => {
                camel_ty.extend(c.to_uppercase());
                last_char_was_underscore = false;
            }
            c => camel_ty.extend(c.to_lowercase()),
        }
    }

    camel_ty.shrink_to_fit();
    camel_ty
}
