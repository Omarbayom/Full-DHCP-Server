# RFC-Compliant DHCP Server Agent
This project implements a DHCP (Dynamic Host Configuration Protocol) server that is compliant with RFC 2131 and RFC 2132. The server dynamically assigns IP addresses to clients and supports advanced DHCP features such as lease management, IP pool configuration, and error handling. The project includes both server and client implementations, along with graphical user interfaces (GUIs) for ease of use.

## Team Members
- [@Seif-Yasser-Ahmed](https://github.com/Seif-Yasser-Ahmed)
- [@Omarbayom](https://github.com/Omarbayom)
- [@Salah1174](https://github.com/Salah1174)
- [@JoeCode11](https://github.com/JoeCode11)

## Contribution
All team members contributed equally to the overall project, ensuring a balanced distribution of tasks and responsibilities. Below is a detailed breakdown of each member's contributions, highlighting the specific areas of work they focused on during the project.

| Name           |Contribution                                |
|----------------|---------------------------------------------|
| **Omar Ahmed** |  Developed the base server functionalities, ensuring the core operations of the DHCP server were robust and efficient. |
| **Seif Yasser**|  Implemented the virtual client and managed the integration of real clients with the server, focusing on seamless client-server communication. |
| **Mohammed Salah** |  Handled the implementation of DHCP options, extending the server's capability to configure network parameters like subnet masks, DNS servers, and gateways, and established a connection via WIFI with an android phone.  |
| **Youssef Tamer** |  Designed and developed the graphical user interface (GUI), enhancing the user experience and providing intuitive controls for server and client operations. |

## Project Structure
```
└── RFC-Compliant-Server-Agent/
├── README.md
├── LICENSE
├── contributing.md
├── requirements.txt
├── docs/
│   ├── RFC2131_summary.md
│   └── RFC2132_summary.md
└── src/
    ├── client/
    │   ├── init.py
    │   ├── client.py
    │   ├── client_config.py
    │   ├── client_gui.py
    │   └── utils.py
    └── server/
        ├── init.py
        ├── blocked_mac.txt
        ├── ip_pool.txt
        ├── server.py
        ├── server_config.py
        ├── server_gui.py
        └── utils.py
```
## Installation and User Usage Guide

### Installation
1. Clone the Repository:
   ```bash
   git clone https://github.com/Seif-Yasser-Ahmed/RFC-Compliant-Server-Agent.git
   cd RFC-Compliant-Server-Agent
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
- **To Open Server's GUI:**
  ```bash
  python src/server/server_gui.py
  ```

- **To Open Client's GUI:**
  ```bash
  python src/client/client_gui.py
  ```

- **To Run The Server in Terminal:**
  ```bash
  python src/server/server.py
  ```

- **To Run The Client in Terminal:**
  ```bash
  python src/client/client.py
  ```

## Roadmap

### Project Planning and Design
- **Objective**: Define the project scope, goals, and functionalities. Develop a detailed design document outlining the architecture, components, and communication protocols.
- **Achievements**:
  - Defined project objectives and scope.
  - Developed a comprehensive design document with system architecture and protocols.

### Basic Client-Server Setup
- **Objective**: Implement the foundational elements of the system, including basic client-server communication using Python and sockets.
- **Achievements**:
  - Implemented a basic server capable of handling multiple client connections.
  - Established TCP connection for basic RFC features.

### Extend Server Features
- **Objective**: Enhance the server with advanced features and error codes as specified in the relevant RFCs.
- **Achievements**:
  - Supported dynamic IP allocation with precise lease durations.
  - Configured additional parameters like domain name and DNS servers.
  - Handled errors with RFC-compliant codes for various scenarios.

### Server Optimization
- **Objective**: Optimize communication protocols for better performance based on different scenarios, ensuring efficient and reliable server-client interactions.
- **Achievements**:
  - Optimized TCP and UDP usage for enhanced performance.
  - Conducted extensive performance testing.
  - Finalized a user-friendly interface for better usability.

### Presentation and Documentation
- **Objective**: Compile and present the completed project, highlighting learned concepts and demonstrating implemented features.
- **Achievements**:
  - Finalized the codebase with clean and well-documented code.
  - Created comprehensive user documentation for installation and configuration.
  - Developed presentation materials showcasing the server’s capabilities and design.

## Documentation
- [Phase 1](https://drive.google.com/file/d/1ClTFydsEEWL7uvOUggPlx6osTgWdA_r3/view?usp=drive_link)
- [Phase 2](https://drive.google.com/file/d/1WqLEdGrZj1wAxTQX6SMTMlkCWzyZshGu/view?usp=drive_link)
- [Phase 3](https://drive.google.com/file/d/17odP42jeeAXGkYLvlgNXzrzAXsOb1d0s/view?usp=drive_link)
- [Phase 4](https://drive.google.com/file/d/1nyslLbnu_CQ_gIe3M1KlEIw7b4U_CBeE/view?usp=drive_link)

## References
- [RFC 2131 - Dynamic Host Configuration Protocol](https://tools.ietf.org/html/rfc2131)
- [RFC 2132 - DHCP Options and BOOTP Vendor Extensions](https://tools.ietf.org/html/rfc2132)
## License
This project is licensed under the terms of the MIT license. See the [`LICENSE`](LICENSE) file for details.
