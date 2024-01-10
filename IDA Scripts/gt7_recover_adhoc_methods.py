import ida_range

# This is called from main() - addresses are for 1.00 (EU)
# Global class register function is at 0x7F4DC0
CLASS_REGISTER_FUNCS_ADDRS = [0x31ACE60, 0x851370, 0x2C11900, 0x1DD7C80, 0x210C190, 0x2313370, 0x1BE1E60, 0x9213A0, 0x34A80]

#######################################################################

# finds the address of the current assignment instruction by looking backwards.
def find_addr_assignment(addr):
    reg_value = print_operand(addr, 1)
        
    # we have mov <addr>, <register>, look for value assigned to register
    prev_inst = prev_addr(addr)
    while 1:
        inst_op = print_operand(prev_inst, 0)

        if inst_op != reg_value: # check same register
           prev_inst = prev_head(prev_inst)
           continue
           
        return prev_inst
    
# finds the first write data ref to the specified address
def get_write_xref(addr):
    dref = get_first_dref_to(addr);

    while 1:
        #print("Dref: " + hex(dref) + " (" + generate_disasm_line(dref, 0) + ")")
        
        # Look for assignment to class ptr
        op = get_operand_value(dref, 0)
        if op != addr: 
           dref = get_next_dref_to(addr, dref)
           continue
           
        return dref;
           
def process_func_table_info(class_name, table_addr, index):
    entry_offset = table_addr + (index * 0x18)
        
    # Read function table
    type_maybe = get_qword(entry_offset)
    func_info_ptr = get_qword(entry_offset + 0x08)
    name_ptr = get_qword(entry_offset + 0x10)
        
    fop = get_item_size(func_info_ptr)
    if fop == 0x20:
        return
        
    # Get the function  name
    func_name = get_strlit_contents(name_ptr, -1, STRTYPE_C).decode("utf-8")
        
    # Find actual function subroutine for this class function (at field 0x28)
    func_ptr_write_xref = get_write_xref(func_info_ptr + 0x28)
    func_ptr_assign_inst_addr = find_addr_assignment(func_ptr_write_xref)
    func_ptr = get_operand_value(func_ptr_assign_inst_addr, 1)


    # Set function name.
    set_name(func_ptr, class_name + "::" + func_name,  idaapi.SN_NOWARN | idaapi.SN_NOCHECK | idaapi.SN_FORCE)
    print("- {:08x} ({:08x}): {}".format(entry_offset, func_ptr, class_name + "::" + func_name));

def process_adhoc_class(class_ptr):
    print("Processing class ptr {}".format(hex(class_ptr)))
    
    '''
    0x00 = class/object name
    0x38 = number of members
    0x40 = members ptr
    0x68 = bits - function count
    0x70 = function table ptr
    '''
    
    # We have the pointer to the class info, search xrefs to it for a write
    # Class name is always assigned at 0x00 of the class info structure
    class_write_xref = get_write_xref(class_ptr)
    name_assign_instruction_addr = find_addr_assignment(class_write_xref)
        
    # We have the pointer to the object name.
    name_ptr = get_operand_value(name_assign_instruction_addr, 1)
    class_name = get_strlit_contents(name_ptr, -1, STRTYPE_C).decode("utf-8")
    print("Class '{}' (assigned at {:08x}) {:08x}".format(class_name, name_assign_instruction_addr, name_ptr))
        
    # Set the class name to the class info ptr.
    ida_name.set_name(class_ptr, class_name + "_class", idaapi.SN_NOWARN | idaapi.SN_NOCHECK | idaapi.SN_FORCE)
    
    # Now, get number of functions in class
    class_func_num_write_xref = get_write_xref(class_ptr + 0x68)
    class_func_num_assign_inst_addr = find_addr_assignment(class_func_num_write_xref)
    class_func_num_bits = get_operand_value(class_func_num_assign_inst_addr, 1)
    
    # unpack bits
    num_func_1 = class_func_num_bits & 0xFFFF
    num_func_2 = (class_func_num_bits >> 16) & 0xFFFF
    ctor_entry_index = (class_func_num_bits >> 32) & 0xFFFF
    dtor_entry_index = (class_func_num_bits >> 48) & 0xFFFF
    
    # Get function table
    class_func_table_write_xref = get_write_xref(class_ptr + 0x70)
    class_func_table_assign_inst_addr = find_addr_assignment(class_func_table_write_xref)
    class_func_table_addr = get_operand_value(class_func_table_assign_inst_addr, 1)
    
    print("Func Table Addr: {:08x} count {}".format(class_func_table_addr, str(num_func_2)))
    
    # Process function/methods, ctor, dtor
    for n in range(0, num_func_1 + num_func_2):
        process_func_table_info(class_name, class_func_table_addr, n)
        
    if ctor_entry_index != 0xFFFF:
        process_func_table_info(class_name, class_func_table_addr, ctor_entry_index)
    if dtor_entry_index != 0xFFFF:
        process_func_table_info(class_name, class_func_table_addr, dtor_entry_index)

###############################################
## Main Loop
###############################################
for func_addr in CLASS_REGISTER_FUNCS_ADDRS:
    # Iterate through function that registers all adhoc modules
    func = idaapi.get_func(func_addr)
    lck = idaapi.lock_func(func)
    limits = ida_range.range_t()
    rs = ida_range.rangeset_t()
    
    if ida_funcs.get_func_ranges(rs, func) != ida_idaapi.BADADDR:
        limits.start_ea = rs.begin().start_ea
        limits.end_ea = rs.begin().end_ea
    else:
        print("error")
        
    # Get instruction that assign to a class ptr
    cur_addr = limits.start_ea
    while cur_addr < limits.end_ea:
        op = print_insn_mnem(cur_addr)
        
        # search for lea then call
        if op == "lea":
            lookahead = next_head(cur_addr)
            if print_insn_mnem(lookahead) != "call":
                break
                
            ptr = get_operand_value(cur_addr, 1)
            process_adhoc_class(ptr)
    
        cur_addr = next_head(cur_addr)
