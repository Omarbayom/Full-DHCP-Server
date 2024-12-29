SERVER_PORT = 67
CLIENT_PORT = 68
BUFFER_SIZE = 1024


test_cases = {
    "Basic_DISCOVER_no_lease": {
        'inputs': [None, None],
        'expected_output': ["192.168.1.100", "ACK", None],
        'pass': False
    },
    "Basic_DISCOVER_with_lease": {
        'inputs': [None, 30],
        'expected_output': ["192.168.1.101", "ACK", 30],
        'pass': False
    },
    "Specific_IP_Request_no_lease": {
        'inputs': ["192.168.1.102", None],
        'expected_output': ["192.168.1.102", "ACK", None],
        'pass': False
    },
    "Specific_IP_Request_with_lease": {
        'inputs': ["192.168.1.103", 300],
        'expected_output': ["192.168.1.103", "ACK", 300],

        'pass': False
    },
    "IP_Already_Assigned": {
        'inputs': ["192.168.1.103", 30],
        'expected_output': ["192.168.1.104", "ACK", 30],

        'pass': False
    },

    "No_Free_IP": {
        'inputs': [None, 30],
        'expected_output': ["", "NACK", 30],

        'pass': False
    },
    "Wait_For_Lease": {
        'inputs': [None, 30],
        'expected_output': ["", "ACK", 30],
    },
    "Non_Existant_IP": {
        'inputs': ["192.168.1.115", 30],
        'expected_output': ["", "ACK", 30],

        'pass': False
    },

    # "RELEASE_IP": {
    #     'inputs': [None, None],
    #     'expected_output': ["192.169.1.100", "ACK", 60],

    #     'pass': False
    # },
}
