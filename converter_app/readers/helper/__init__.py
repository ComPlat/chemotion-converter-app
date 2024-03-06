def get_shape(row):
    """Get shap of a row (see excel and old_excel reader)"""
    shape = []
    for cell in row:
        if cell is None:
            shape.append(None)
        else:

            if isinstance(cell, (int, float)):
                shape.append('f')
            else:
                shape.append('s')
    return shape
