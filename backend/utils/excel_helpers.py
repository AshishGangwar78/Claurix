def column_number_to_excel(col_num): #this is for changing column no. to colmun name

    result = ""# example 1 to A , 28 to AB

    while col_num > 0:

        col_num, remainder = divmod(
            col_num - 1,
            26
        )

        result = chr(
            65 + remainder
        ) + result

    return result
