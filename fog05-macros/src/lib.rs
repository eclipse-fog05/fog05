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
struct MacroArgs {
    timeout_s: u16,
    #[darling(default)]
    prefix : Option<String>
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
    let macro_args = match MacroArgs::from_list(&attr_args) {
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

    //service uuid
    let uuid = Uuid::new_v4();

    //service eval path
    let path = match macro_args.prefix {
        Some(prefix) => format!("{}/zservice/{}/uuid/{}/serve",prefix, ident, uuid).to_string(),
        None => format!("/zservice/{}/uuid/{}/serve", ident, uuid).to_string(),
    };

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
        uuid,
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
    uuid : Uuid,                            //uuid of this service
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

                //Serve function that returs the object that implements the actual serve function
                fn serve(self) -> #server_ident<Self>{
                    #server_ident {service:self}
                }
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
                service: S,
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
            ..
        } = self;

        quote!{
            impl<S> fog05_sdk::services::ZServe<#request_ident> for #server_ident<S>
            where S: #service_ident + Send +'static
            {
                type Resp = #response_ident;
                fn serve(self, locator : String) {
                    async_std::task::block_on(async {
                        let zenoh = zenoh::Zenoh::new(zenoh::config::client(Some(locator))).await.unwrap();
                        let ws2 = zenoh.workspace(None).await.unwrap();
                        // path as to be generated for this server this is an initial test
                        let path = zenoh::Path::try_from(format!("{}",#eval_path)).unwrap();
                        let mut rcv = ws2.register_eval(&path.into()).await.unwrap();
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
                                            #service_ident::#method_idents(self.service.clone(), #(#arg_pats),*));
                                        let encoded = bincode::serialize(&resp).unwrap();
                                        let p = zenoh::Path::try_from(get_request.selector.path_expr.as_str()).unwrap();
                                        get_request.reply(p.into(), encoded.into()).await;
                                    }
                                )*
                            }
                        }
                    });
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
            #vis struct #client_ident<'a, C = fog05_sdk::services::ZClientChannel<'a, #request_ident, #response_ident>>{
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
                    ws : async_std::sync::Arc<zenoh::Workspace>
                ) -> #client_ident {
                        let new_client = fog05_sdk::services::ZClientChannel::new(ws, format!("{}",#eval_path));
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