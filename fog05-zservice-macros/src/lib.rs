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

extern crate darling;
extern crate proc_macro;
extern crate proc_macro2;
extern crate quote;
extern crate syn;
extern crate serde;
extern crate bincode;
extern crate serde_json;
extern crate base64;


use proc_macro::TokenStream;
use proc_macro2::{Span, TokenStream as TokenStream2};
use quote::{format_ident, quote, ToTokens};
use uuid::Uuid;
use std::str::FromStr;
use darling::FromMeta;
use syn::{
    AttributeArgs,
    braced,
    ext::IdentExt,
    parenthesized,
    parse::{Parse, ParseStream},
    parse_macro_input, parse_quote,
    spanned::Spanned,
    token::Comma,
    Attribute, FnArg, Ident, ImplItem, ImplItemMethod, ImplItemType, ItemImpl,
    Pat, PatType, ReturnType, Token, Type, Visibility,
};




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
    prefix : Option<String>
}


#[derive(Debug, FromMeta)]
struct ZServerMacroArgs {
    #[darling(default)]
    uuid : Option<String>
}

struct ZService {
    attrs: Vec<Attribute>,
    vis : Visibility,
    ident : Ident,
    evals : Vec<EvalMethod>
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

struct EvalMethod{
    attrs : Vec<Attribute>,
    ident : Ident,
    args : Vec<PatType>,
    output : ReturnType
}

impl Parse for EvalMethod {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let attrs = input.call(Attribute::parse_outer)?;
        input.parse::<Token![async]>()?;
        input.parse::<Token![fn]>()?;
        let ident = input.parse()?;
        let content;
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
                FnArg::Receiver(_) => {
                    extend_errors!(
                        errors,
                        syn::Error::new(arg.span(), "method args cannot start with self")
                    );
                }
            }
        }
        errors?;
        let output = input.parse()?;
        input.parse::<Token![;]>()?;

        Ok(Self {
            attrs,
            ident,
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
pub fn zservice(_attr : TokenStream, input : TokenStream) -> TokenStream {
    let unit_type : &Type = &parse_quote!(());

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
        Err(e) => { return TokenStream::from(e.write_errors()); }
    };

    //converts the functions names from snake_case to CamelCase
    let camel_case_fn_names: &Vec<_> = &evals
        .iter()
        .map(|eval| snake_to_camel(&eval.ident.unraw().to_string()))
        .collect();

    // Collects the pattern for the types
    let args : &[&[PatType]] = &evals.iter().map(|eval| &*eval.args).collect::<Vec<_>>();

    //service eval path
    let path = match macro_args.prefix {
        Some(prefix) => format!("{}/zservice/{}/",prefix, ident).to_string(),
        None => format!("/zservice/{}/", ident).to_string(),
    };

    let service_name = format!("{}Service", ident);
    // Generates the code
    let ts : TokenStream = ZServiceGenerator{
        service_ident: ident,
        server_ident: &format_ident!("Serve{}", ident), //Server is called Serve<Trait Name>
        client_ident: &format_ident!("{}Client", ident), //Client is called <Trait Name>Client
        request_ident: &format_ident!("{}Request", ident), //Request type is called <Trait Name>Request
        response_ident: &format_ident!("{}Response", ident), //Response type is called <Trait Name>Response
        vis,
        args,
        method_attrs: &evals.iter().map(|eval| &*eval.attrs).collect::<Vec<_>>(), //getting evals attributes
        method_idents: &evals.iter().map(|eval| &eval.ident).collect::<Vec<_>>(), //getting evals names
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
        timeout : &macro_args.timeout_s,
        eval_path : &path,
        service_name : &service_name,
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


    let attr_args = parse_macro_input!(_attr as AttributeArgs);
    let macro_args = match ZServerMacroArgs::from_list(&attr_args) {
        Ok(v) => v,
        Err(e) => { return TokenStream::from(e.write_errors()); }
    };

    let mut expected_non_async_types: Vec<(&ImplItemMethod, String)> = Vec::new();
    let mut found_non_async_types: Vec<&ImplItemType> = Vec::new();

    for inner in &mut item.items {
        match inner {
            ImplItem::Method(method) => {
                if method.sig.asyncness.is_some() {
                    // if this function is declared async, transform it into a regular function
                    method.sig.asyncness = None
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

    let uuid = match macro_args.uuid {
        Some(u) => Uuid::from_str(&u).unwrap(),
        None => Uuid::new_v4(),
    };

    let str_uuid = format!("{}", uuid);

    let uuid_imp = TokenStream::from(
        quote!{
        fn instance_uuid(&self) -> uuid::Uuid {
            Uuid::from_str(#str_uuid).unwrap()
        }
    });

    let method = syn::parse_macro_input!(uuid_imp as syn::ImplItemMethod);

    item.items.push(ImplItem::Method(method));

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
        if provided
            .iter()
            .find(|typedecl| typedecl.ident == expected)
            .is_none()
        {
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
    service_ident : &'a Ident,              //service type
    server_ident : &'a Ident,               //server type
    client_ident : &'a Ident,               //client type
    request_ident : &'a Ident,              //request type
    response_ident : &'a Ident,             //response type
    vis : &'a Visibility,                   //visibility
    attrs : &'a [Attribute],                //attributes
    evals : &'a [EvalMethod],               //functions to be exposed via evals
    camel_case_idents: &'a [Ident],         //camel case conversion of all names
    method_idents : &'a [&'a Ident],        //type of the methods
    method_attrs : &'a [&'a [Attribute]],   //attributes of the methods
    args : &'a [&'a [PatType]],             // types description pattern
    return_types: &'a [&'a Type],           // return types of functions
    arg_pats: &'a [Vec<&'a Pat>],           // patterns for args
    timeout: &'a u16,                       //eval timeout
    eval_path : &'a String,                 //path for evals
    service_name : &'a String,              //service name on zenoh
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
            ..
        } = self;

        let fns = evals
            .iter()
            .zip(return_types.iter())
            .map(
                |(EvalMethod{attrs,ident,args,..},output,)|
                {

                    quote! {

                        #(#attrs)*
                        fn #ident(self, #(#args),*) -> #output;
                    }
                },
            );

        quote!{
            #(#attrs)*
            #vis trait #service_ident : Clone{
                #(#fns)*

                /// Returns the server object
                fn get_server(self, z : async_std::sync::Arc<zenoh::Zenoh>) -> #server_ident<Self>{
                    #server_ident {
                        server : self,
                        z : z,
                    }
                }

                /// Returns the service instance uuid
                fn instance_uuid(&self) -> uuid::Uuid;

            }
        }
    }

    //creates the server struct
    fn struct_server(&self) -> TokenStream2 {
        let &Self{
            vis, server_ident, ..
        } = self;

        quote!{
            #[derive(Clone)]
            #vis struct #server_ident<S> {
                z : async_std::sync::Arc<zenoh::Zenoh>,
                server: S,
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

        quote!{
            impl<S> fog05_zservice::ZServe<#request_ident> for #server_ident<S>
            where S: #service_ident + Send +'static
            {

                type Resp = #response_ident;


                fn connect(&self){
                    task::block_on(
                        async {
                            let zsession = self.z.session();
                            let zinfo = zsession.info().await;
                            let rid = hex::encode(&(zinfo.iter().find(|x| x.0 == zenoh::net::info::ZN_INFO_ROUTER_PID_KEY ).unwrap().1));
                            let pid = hex::encode(&(zinfo.iter().find(|x| x.0 == zenoh::net::info::ZN_INFO_PID_KEY).unwrap().1));
                            let ws = self.z.workspace(None).await.unwrap();
                            let component_advertisement = fog05_zservice::ComponentAdvertisement{
                                uuid : self.server.instance_uuid(),
                                name : format!("{}", #service_name),
                                routerid : rid.clone(),
                                peerid : pid.clone(),
                            };
                            let encoded_ca = bincode::serialize(&component_advertisement).unwrap();
                            let path = zenoh::Path::try_from(format!("/{}/{}/info",#eval_path,self.server.instance_uuid())).unwrap();
                            ws.put(&path.into(),encoded_ca.into()).await.unwrap();

                            let component_info = fog05_zservice::ComponentInformation{
                                uuid : self.server.instance_uuid(),
                                name : format!("{}", #service_name),
                                routerid : rid.clone(),
                                peerid : pid.clone(),
                                status : fog05_zservice::ComponentStatus::HALTED,
                            };
                            let encoded_ci = bincode::serialize(&component_info).unwrap();
                            let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                        }
                    );
                }


                fn authenticate(&self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::HALTED => {
                                                    ci.status = fog05_zservice::ComponentStatus::BUILDING;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than HALTED"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn register(&self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::BUILDING => {
                                                    ci.status = fog05_zservice::ComponentStatus::REGISTERED;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than BUILDING"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn announce(&self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::REGISTERED => {
                                                    ci.status = fog05_zservice::ComponentStatus::ANNOUNCED;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than REGISTERED"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn work(&self) ->  (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
                    task::block_on(
                        async {
                            let (s, r) = async_std::sync::channel::<()>(1);
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::ANNOUNCED => {
                                                    ci.status = fog05_zservice::ComponentStatus::WORK;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                    let server = self.clone();
                                                    let h = async_std::task::spawn( async move {
                                                        server.serve(r);
                                                    });
                                                    (s,h)
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than ANNOUNCED"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    )
                }


                fn serve(&self, stop : async_std::sync::Receiver<()>) {
                    task::block_on(async {
                        let ws = self.z.workspace(None).await.unwrap();
                        let path = zenoh::Path::try_from(format!("{}/{}/eval",#eval_path, self.server.instance_uuid())).unwrap();
                        let mut rcv = ws.register_eval(&path.clone().into()).await.unwrap();
                        let rcv_loop = async {
                            loop {
                                let get_request = rcv.next().await.unwrap();
                                let base64_req = get_request.selector.properties.get("req").cloned().unwrap();
                                let b64_bytes = base64::decode(base64_req).unwrap();
                                let js_req = str::from_utf8(&b64_bytes).unwrap();
                                let req = serde_json::from_str::<#request_ident>(&js_req).unwrap();

                                match req {
                                    #(
                                        #request_ident::#camel_case_idents{#(#arg_pats),*} => {
                                            let resp = #response_ident::#camel_case_idents(
                                                #service_ident::#method_idents(self.server.clone(), #(#arg_pats),*));
                                            let encoded = bincode::serialize(&resp).unwrap();
                                            get_request.reply(path.clone().into(), encoded.into()).await;
                                        }
                                    )*
                                }
                            }
                        };
                        rcv_loop.race(stop.recv()).await.unwrap();
                    });
                }

                fn unwork(&self, stop : async_std::sync::Sender<()>){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::WORK => {
                                                    ci.status = fog05_zservice::ComponentStatus::UNWORK;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                    stop.send(()).await;
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than WORK"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn unannounce(&self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::UNWORK => {
                                                    ci.status = fog05_zservice::ComponentStatus::UNANNOUNCED;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than UNWORK"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn unregister(&self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::UNANNOUNCED => {
                                                    ci.status = fog05_zservice::ComponentStatus::UNREGISTERED;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than UNANNOUNCED"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
                }

                fn disconnect(self){
                    task::block_on(
                        async {
                            let selector = zenoh::Selector::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                            let ws = self.z.workspace(None).await.unwrap();
                            let mut ds = ws.get(&selector).await.unwrap();
                            let mut data = Vec::new();
                            while let Some(d) = ds.next().await {
                                data.push(d)
                            }
                            match data.len() {
                                0 => panic!("This component state is not present in Zenoh!!"),
                                1 => {
                                    let kv = &data[0];
                                    match &kv.value {
                                        zenoh::Value::Raw(_,buf) => {
                                            let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                            match ci.status {
                                                fog05_zservice::ComponentStatus::UNREGISTERED => {
                                                    ci.status = fog05_zservice::ComponentStatus::DISCONNECTED;
                                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                                    let path = zenoh::Path::try_from(format!("/{}/{}/state",#eval_path,self.server.instance_uuid())).unwrap();
                                                    ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                                },
                                                _ => panic!("Cannot authenticate a component in a state different than UNREGISTERED"),
                                            }
                                        },
                                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                                    }
                                },
                                _ => unreachable!(),
                            }
                        }
                    );
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
            #[derive(Debug, serde::Serialize, serde::Deserialize)]
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
            #[derive(Debug, serde::Serialize, serde::Deserialize)]
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
            #vis struct #client_ident<'a, C = fog05_zservice::ZClientChannel<'a, #request_ident, #response_ident>>{
                ch : C,
                phantom : std::marker::PhantomData<&'a ()>
            }
        }
    }


    // Generates the implentation of the client
    fn impl_client_new(&self) -> TokenStream2 {
        let &Self {
            client_ident,
            vis,
            eval_path,
            ..
        } = self;

        quote! {
            impl #client_ident<'_> {
                #vis fn new(
                    ws : async_std::sync::Arc<zenoh::Workspace>,
                    instance_id : uuid::Uuid
                ) -> #client_ident {
                        let new_client = fog05_zservice::ZClientChannel::new(ws, format!("{}/{}/eval",#eval_path, instance_id));
                        #client_ident{
                            ch : new_client,
                            phantom : std::marker::PhantomData,
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
            args,
            return_types,
            arg_pats,
            camel_case_idents,
            timeout,
            ..
        } = self;

        quote! {
            impl #client_ident<'_> {
                #(
                    #[allow(unused)]
                    #( #method_attrs )*
                    #vis fn #method_idents(&mut self, #( #args ),*)
                        -> impl std::future::Future<Output = std::io::Result<#return_types>> + '_ {
                        let request = #request_ident::#camel_case_idents { #( #arg_pats ),* };
                        let resp = self.ch.call_fun(request);
                        async move {
                            let dur = std::time::Duration::from_secs(#timeout as u64);
                            match async_std::future::timeout(dur, resp).await {
                                Ok(r) => match r {
                                    Ok(zr) => match zr {
                                            #response_ident::#camel_case_idents(msg) => std::result::Result::Ok(msg),
                                            _ => unreachable!(),
                                        },
                                    Err(e) => Err(e),
                                },
                                Err(e) => Err(std::io::Error::new(std::io::ErrorKind::TimedOut, format!("{}", e))),
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
            self.impl_client_new(),
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