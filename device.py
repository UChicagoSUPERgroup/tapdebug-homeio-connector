class Device(object):
    def __init__(self, typ, datatype, address, name):
        self.address = address
        self.typ = typ
        self.datatype = datatype
        self.name = name

    def __str__(self):
        return str(self.typ) + '|' + str(self.datatype) + '|' + str(self.address) + '|' + str(self.name)
    
    def __hash__(self) -> int:
        return hash(str(self.typ) + '|' + str(self.datatype) + '|' + str(self.address))

    def __eq__(self, o: object) -> bool:
        return type(self) == type(o) and self.address == o.address and self.typ == o.typ and self.datatype == o.datatype


def init_dev_list():
    input_bit_dev_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 
                         16, 17, 27, 28, 29, 39, 49, 50, 51, 52, 53, 54, 55, 
                         56, 57, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 
                         78, 79, 80, 81, 82, 92, 93, 94, 95, 96, 97, 98, 99, 
                         100, 101, 102, 112, 113, 114, 115, 116, 117, 118, 119, 
                         120, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 
                         140, 150, 151, 152, 153, 163, 164, 165, 166, 167, 168, 
                         169, 170, 171, 172, 173, 183, 184, 185, 195, 196, 197, 
                         198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 217, 
                         218, 219, 220, 221, 222, 223, 233, 234, 235, 236, 237, 
                         238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 
                         258, 259, 260, 261, 262, 263, 264, 274, 275, 276, 277,
                         278, 279]
    input_float_dev_ids = [0, 1, 2, 3, 4, 5, 6, 12, 13, 14, 15, 24, 25, 26, 27, 
                           36, 37, 46, 47, 48, 57, 58, 59, 60, 69, 70, 80, 81, 
                           82, 83, 92, 93, 103, 104, 105, 106, 115, 116, 117, 
                           118, 127, 128, 129, 130, 139]
    input_datetime_dev_ids = [0]
    output_bit_dev_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 19, 20, 30, 40, 41, 42, 
                          43, 44, 54, 55, 56, 57, 58, 59, 60, 68, 69, 70, 71, 
                          72, 73, 83, 84, 85, 86, 87, 97, 98, 99, 100, 110, 111, 
                          112, 122, 123, 124, 125, 135, 136, 146, 147, 148, 149, 
                          159, 160, 161, 162, 172, 173, 174, 175, 176, 177, 187, 
                          188, 189, 190, 191, 192, 193, 194]
    output_float_dev_ids = [0, 1, 11, 12, 22, 32, 33, 34, 44, 45, 55, 56, 66, 
                            67, 68, 78, 79, 89, 90, 91, 101, 102, 112, 113, 
                            123, 124, 134, 135, 145, 146, 147, 148, 158, 159, 
                            160, 161, 162]
    shade_dev_ids = [1000, 1001, 1002, 1003, 1004,
                          1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012]
    garage_door_dev_ids = [1013, 1014]
    alarm_key_pad_dev_ids = [1015]

    dev_list = []
    virtual_dev_list = []  # handle the high-level devices for shades and garages

    input_data_types = ['Bit', 'Float', 'DateTime']
    input_lists = [input_bit_dev_ids, input_float_dev_ids, input_datetime_dev_ids]
    
    
    for data_type, input_list in zip(input_data_types, input_lists):
        for dev_id in input_list:
            device = Device('Input', data_type, dev_id, '')
            dev_list.append(device)

    output_data_types = ['Bit', 'Float']
    output_lists = [output_bit_dev_ids, output_float_dev_ids]
    for data_type, output_list in zip(output_data_types, output_lists):
        for dev_id in output_list:
            device = Device('Output', data_type, dev_id, '')
            dev_list.append(device)
    
    for dev_id in shade_dev_ids + garage_door_dev_ids + alarm_key_pad_dev_ids:
        device = Device('Output', 'Bit', dev_id, '')
        virtual_dev_list.append(device)
    return dev_list, virtual_dev_list
