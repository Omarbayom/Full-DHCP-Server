# RFC-Compliant-Server-Agent
 Analyzing and implementing a server agent for DHCP, DNS, or HTTP/2 protocols that is compliant with the RFC

 ## Team Members
>  -  [Seif Yasser](https://github.com/Seif-Yasser-Ahmed)
>  -  [Mohamed Salah](https://github.com/Salah1174)
>  -  [Omar Ahmed](https://github.com/Omarbayom)
>  -  [Youssef Tamer](https://github.com/JoeCode11)

## Phases
1. [ ] Project Planning and Design
2. [ ] Basic Client-Server Setup
3. [ ]  Extend Server features
3. [ ]  Server Optimization
-----
### Project Planning and Design
 Define the project scope, goals, and functionalities. Create a detailed design document 
outlining the architecture, components, and communication protocols. 

#### Steps
- Define user authentication mechanisms. 
- Outline the overall project scope, including key functionalities. 
- Design the system architecture, specifying components and their interactions. 
- Demonstrate communication/message protocols according to the RFC.

### Basic Client-Server Setup
Implement the foundational elements of the system, including basic client-server 
communication using Python and sockets. 

#### Steps 
- Implement a basic server application capable of handling multiple client connections. 
- Establish a TCP connection for user authentication (if required). 
- Implement a simple command-line interface showing the server status. 

### Extend Server features
extend the developed server agent with RFC features and error codes.


### Server Optimization
Enhance the developed agent by optimizing communication protocols for better 
performance according to the RFC.
#### Steps 
- Optimize communication protocols based on different scenarios (e.g., TCP for reliability, UDP 
for real-time interactions).
- Conduct performance testing to evaluate the scalability of the system. 
- Finalize the user interface, considering usability and user experience. 

-----

## Backlog of Requirements and User Stories are according to the RFC. 
RFCs can be found [here](https://datatracker.ietf.org/))

### HTTP/2 (HTTP/2.0) 

- **RFC 7540**: Hypertext Transfer Protocol Version 2 (HTTP/2). This RFC specifies HTTP/2, a major 
revision of the HTTP network protocol, designed to improve performance over its predecessor 
HTTP/1.1. HTTP/2 introduces features like multiplexing of requests, header compression, and server 
push. It aims to reduce latency and improve the overall web browsing experience while maintaining 
compatibility with HTTP/1.1 semantics.  <br>

- **RFC 7541**: HPACK: Header Compression for HTTP/2. This document defines HPACK, the header 
compression algorithm used by HTTP/2. It focuses on reducing the size of headers and improving 
performance in situations where large headers need to be transferred.

### Dynamic Host Configuration Protocol (DHCP)

- **RFC 2131**: Dynamic Host Configuration Protocol (DHCP) defines DHCP, a protocol used to automate 
the assignment of IP addresses, subnet masks, gateways, and other network parameters. It allows 
devices on a network to request configuration information from a DHCP server dynamically.

- **RFC 2132**: DHCP Options and BOOTP Vendor Extensions. This RFC details additional options that 
can be used with DHCP, extending the base protocol to support various configuration parameters 
such as subnet masks, routers, and domain names. 

### Domain Name System (DNS) 

- **RFC 1034**: Domain Names – Concepts and Facilities. This foundational RFC defines the concept of 
the Domain Name System (DNS), which is responsible for translating human-readable domain 
names into IP addresses. It outlines the basic structure and operation of DNS.

- **RFC 1035**: Domain Names – Implementation and Specification. This RFC provides detailed 
specifications for the DNS protocol, including message formats, query types, and response 
structures. It focuses on how the DNS protocol operates in practice.

- **RFC 2181**: Clarifications to the DNS Specification. This RFC clarifies ambiguities and updates certain 
aspects of the original DNS specification (RFC 1034 and RFC 1035) to address issues encountered 
during deployment.

> :bulb: **Tip:** Remember to appreciate the little things in life.
