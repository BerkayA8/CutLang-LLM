import os
import re
from itertools import product
import copy


def generate_all_combinations(input):

    """
        generate all possible combinations for the values of the input objects
    """

    combination_list = []

    for block_type, block_objects in input.items():

        for object in block_objects:
            obj_name = object["name"]
                            
            for attr_name, attr_values in object["attr"].items():

                attr_combinations = []

                if isinstance(attr_name, tuple):
                    if not isinstance(attr_values, tuple):
                        raise ValueError()  
                        
                    all_op_tuples = [list(value.keys())[0] for value in attr_values]
                    op_combinations = list(product(*all_op_tuples))

                    all_value_tuples = [list(value.values())[0] for value in attr_values]
                    value_combinations = list(product(*all_value_tuples))


                    for ops in op_combinations:
                        for values in value_combinations:
                            new_comb = (block_type, obj_name, attr_name, ops, values)
                            attr_combinations.append(new_comb)
                    

                else:
                    for operators, values in attr_values.items():
                             
                        if isinstance(operators, tuple):
                            for op in operators:
                                for value in values:
                                    new_comb = (block_type, obj_name, attr_name, op, value)
                                    attr_combinations.append(new_comb)
                        else:
                            for value in values:
                                new_comb = (block_type, obj_name, attr_name, operators, value)
                                attr_combinations.append(new_comb)
                        

                combination_list.append(attr_combinations)
                

    all_combinations = list(product(*combination_list))
    return all_combinations


def extract_features(query_string):
    # The delimiters (used in ternary operators, logic statements etc.)
    delimiters = ["?", ":", " or ", " and "]
    
    # Regex to capture: (LHS) (Operator) (RHS)
    op_pattern = re.compile(r"(.*?)\s*(>=|<=|==|!=|>|<|~=)\s*(.*)")

    
    # Regex to capture initial keyword
    keyword_match = re.match(r'(\s*(select|reject))(\s+)', query_string, re.IGNORECASE)
    
    initial_keyword_token = ""
    cleaned_query = query_string

    # Assemble the final feature list
    results = []
    
    if keyword_match:
        # The full string including leading whitespace and the keyword (eg " select")
        initial_keyword_token = keyword_match.group(1) 
        
        # The required space after the keyword 
        space_after_keyword = keyword_match.group(3)
        
        # Remove the full match (keyword + all spaces) from the original string
        full_match_length = len(keyword_match.group(0))
        cleaned_query = query_string[full_match_length:]

        
        cleaned_query = space_after_keyword + cleaned_query

        # Split the remaining query into atomic chunks
        atomic_statements = []
        current_chunk = ""
        paren_depth = 0
        
        i = 0
        while i < len(cleaned_query):
            char = cleaned_query[i]
            
            if char == '(':
                paren_depth += 1
                current_chunk += char
            elif char == ')':
                paren_depth -= 1
                current_chunk += char
            
            elif paren_depth == 0:
                found_delim = False
                for delim in delimiters:
                    if cleaned_query[i:].startswith(delim):
                        if current_chunk.strip():
                            atomic_statements.append(current_chunk.strip())
                        
                        # Add the delimiter itself as a separate token
                        atomic_statements.append(delim.strip()) 
                        
                        current_chunk = ""
                        i += len(delim) - 1 
                        found_delim = True
                        break
                
                if not found_delim:
                    current_chunk += char
            else:
                current_chunk += char
            
            i += 1
        
        if current_chunk.strip():
            atomic_statements.append(current_chunk.strip())

        
        # Add the initial keyword token with preserved whitespace
        if initial_keyword_token:
            results.append(initial_keyword_token)
        

        for stmt in atomic_statements:
            match = op_pattern.match(stmt)
            
            if match:
                lhs = match.group(1).strip()
                op = match.group(2).strip()
                rhs = match.group(3).strip()
                
                results.extend([lhs, op, rhs])
            else:
                # keep it as a single token (eg 'or', 'and', ':', '?', 'ALL')
                results.append(stmt)
    
    return results


def augment_adl(original_adl, input):
    """ 
        Looping through all possible combinations, generate adl files
    """

    combinations = generate_all_combinations(input)

    with open(original_adl, "r") as file:
        lines = file.readlines()
        extracted_lines = []

        for line in lines:
            extracted_line = extract_features(line)
            extracted_lines.append(extracted_line)


    in_object = False
    object_name = None
    in_region = False
    region_name = None

    lines_to_modify = []

    object_start = re.compile(r'^\s*object\s+\w+') ## ??
    region_start = re.compile(r'^\s*region\s+\w+') ## ??

    object_keywords = ["select", "take", "reject"]
    region_keywords = ["select"] 

    # First, loop through the file once to locate the lines to be modified 
    for i, line in enumerate(lines):
        change_line = False


        if in_object and all(key not in line for key in object_keywords):  # exit
            in_object = False
            object_name = None


        if in_region and all(key not in line for key in region_keywords):  # exit
            in_region = False
            region_name = None


        if object_start.match(line):
            in_object = True     
            object_name = line.split()[1]
            continue

        if region_start.match(line):
            in_region = True     
            region_name = line.split()[1]
            continue


        if in_object or in_region:
            for parameter in combinations[0]:

                if in_object and parameter[0] == "object":
                    if parameter[1] == object_name:

                        if isinstance(parameter[2], tuple): 
                            in_extracted = True
                            for attr in parameter[2]:
                                if attr not in extracted_lines[i]:
                                    in_extracted = False
                            
                            if in_extracted:
                                change_line = True
                        else:
                            if parameter[2] in extracted_lines[i]:
                                change_line = True                  

                if in_region and parameter[0] == "region":
                    if parameter[1] == region_name:

                        if isinstance(parameter[2], tuple):
                            in_extracted = True
                            for attr in parameter[2]:
                                if attr not in extracted_lines[i]:
                                    in_extracted = False
                            
                            if in_extracted:
                                change_line = True
                        else:
                            if parameter[2] in extracted_lines[i]:
                                change_line = True

            if change_line:
                lines_to_modify.append(i)


    os.makedirs('Augmented_ADLs', exist_ok=True)

    # generate an adl file for each combination
    for combination in combinations:
        adl_copy = copy.deepcopy(lines)
        file_name = "Augmented_ADLs/"

        for i, parameter in enumerate(combination):
            attributes = parameter[2]  
            line_to_modify = lines_to_modify[i]
            modified_line_list = extracted_lines[line_to_modify]
            file_name += f"({parameter[3]}:{str(parameter[4])})_"

            attr_counter = {}
            for attr in attributes:
                attr_counter[attr] = 0

            if isinstance(attributes, tuple):
                for j, attr in enumerate(attributes):
                    attr_index_list = [i for i, x in enumerate(extracted_lines[line_to_modify]) if x == attr]
                    attr_index = attr_index_list[attr_counter[attr]]
                    modified_line_list[attr_index + 1] = parameter[3][j]   # change the operator
                    modified_line_list[attr_index + 2] = parameter[4][j]   # change the value

                    attr_counter[attr] += 1
            else:
                attr_index = extracted_lines[line_to_modify].index(attributes)
                modified_line_list[attr_index + 1] = parameter[3]   # change the operator
                modified_line_list[attr_index + 2] = parameter[4]   # change the value

            modified_line = " ".join(str(x) for x in modified_line_list) + "\n"
            adl_copy[line_to_modify] = modified_line

        file_name += ".adl"
        with open(file_name, "w") as new_adl:
            new_adl.writelines(adl_copy)


    return lines_to_modify