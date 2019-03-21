# Introduction

Early Internet of Things (IoT) applications adopted cloud-centric architectures
where information collected from things is processed in a cloud infrastructure and decisions are pushed back from the cloud to things.
While this architectural paradigm is suitable for a subset of Consumer IoT (CIoT),
it quickly shows its limitation in the context of Industrial IoT (IIoT).
More specifically, the following assumptions, at the foundation of cloud-centric architectures, are generally violated in IIoT applications:

- Connectivity
- Latency
- Throughput
- Cost of Connectivity
- Security

## Definition of Fog Computing

Early fog computing initiatives and demonstrations,
focused on enabling cloud-less architectures by leveraging edge infrastructure.
The main aim was exploiting relatively capable edge infrastructure to bring
computing closer to were data was being produced and control needed to be
actuated.
Things were left out of the picture.
In other terms we had moved from a cloud-centric to an edge-centric architecture
but not necessarily toward an end-to-end solution.
The segregation was eventually resolved by the OpenFog Consortium Architecture Working Group in the vision paper, where the authors of this paper, along with the key companies driving fog computing agreed on the definition reported below.


***Fog computing.*** *A system-level architecture that distributes computing,
storage, control and networking functions closer to the users along a
cloud-to-thing continuum*

## Multi-Access Edge Computing

While the IoT community was debating about the need of fog computing,
the telecommunication community started working on the concept of
Multi-Access Edge Computing (MEC).
Whilst MEC and fog computing emerged from different communities the main problem they try to solve is essentially the same,
exception made for few differences w.r.t. the application domain and the induced constraints.
In other terms, MEC aims at providing unified management across the cloud down to the network edge.
Fog computing, on the other end, expands down
to things.
The other big difference, is that as fog computing infrastructures have to deal with industrial real-time applications.
As such, their ability to manage and virtualize resources in a real-time environments is essential.
Beside this differences, MEC and fog computing share very similar requirements, this has been acknowledged by the collaborations between ETSI and the OpenFog
Consortium, announced in September 2017, for driving the convergence.

## fog∅5

In today available fog/edge/cloud infrastructure the main limitations can be summarized as (1) deployment limited mostly to VM and/or Containers,
(2) lack of support for real-time,
(3) lack of mudularity with consequences on extensibility,
and (4) limited security.

**fog∅5** defines a set of abstractions to unify the compute, storage and
network fabric end-to-end and thus allow applications to be managed,
monitored and orchestrated across the cloud to thing continuum.

#### Entity

The kay abstraction is the *entity*. An entity is either an atomic entity,
such as a Virtual Machine, a container, a Unikernel, a binary executable, or a
Directed Acyclic Graph (DAG) of entities (see Figure 1). Where the set of atomic entities supported by fog∅5 can be extended through plugins.

#### Resources

fog∅5 uses resources, expressed as URI, to represent everything in the system.
In the URI it is possible to have wildcards, query and fragments.
Sub-resources can be nested, some types of resources and sub-resources are reserved and used by the fog∅5 agent.
Two types of wildcards are allowed:

- * to indicate an arbitrary sub-path of length 1.
- ** to indicate a sub-path of arbitrary length.

#### Distributed KV Store

Each fog∅5 node has an instance of a distributed KV store used for the IPC and for store information about the current status of the system.
There is no master node, node act as pairs, complex managment and orchestration
can be implemented on top.

#### Plugins

All the components of fog05 can be extended by plugins, there are interfaces that can be used for the implementation of the plugins, these interface [defined here](https://github.com/eclipse/fog05/tree/master/fog05/interfaces) are for

- OS Plugins
- Deployable units (Runtime) plugins
- Network provisioning plguins
- Monitoring Plugins
- Resoruce Managment (Orchestration)



