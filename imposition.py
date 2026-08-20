import math

def calculate_imposition(images_or_count, rows=2, cols=2, rotate_back=False):
    """
    Calculates book imposition and grid layout for a list of images or image count.

    Implements standard saddle-stitch booklet imposition where physical sheets are folded in half.

    A physical sheet side contains `cols` total columns and `rows` total rows.
    When cols >= 2:
      Each side contains 2 logical pages: Left Page (`left_cols = cols // 2`) and Right Page (`right_cols = cols - left_cols`).
      Thus each sheet contains 4 logical pages (Front Left, Front Right, Back Left, Back Right).
      Total pages per sheet = 4.
    When cols == 1:
      Each side contains 1 logical page. Total pages per sheet = 2.
    """
    if isinstance(images_or_count, int):
        total_images = images_or_count
        image_items = list(range(total_images))
    else:
        image_items = list(images_or_count)
        total_images = len(image_items)

    images_per_side = rows * cols
    images_per_sheet = 2 * images_per_side

    if cols > 1:
        left_cols = cols // 2
        right_cols = cols - left_cols
        pages_per_sheet = 4
    else:
        left_cols = 1
        right_cols = 0
        pages_per_sheet = 2

    left_page_cap = rows * left_cols
    right_page_cap = rows * right_cols if cols > 1 else 0

    if total_images == 0:
        total_sheets = 0
        total_logical_pages = 0
    else:
        total_sheets = math.ceil(total_images / images_per_sheet)
        total_logical_pages = total_sheets * (2 if cols == 1 else 4)

    total_slots = total_sheets * images_per_sheet
    padded_images = image_items + [None] * (total_slots - total_images)

    def get_page_cap(p):
        if cols == 1:
            return images_per_side
        return right_page_cap if (p % 2 == 0) else left_page_cap

    logical_pages = []
    curr_idx = 0
    for p in range(total_logical_pages):
        cap = get_page_cap(p)
        logical_pages.append(padded_images[curr_idx : curr_idx + cap])
        curr_idx += cap

    sheets = []
    M = total_logical_pages

    for s in range(total_sheets):
        if cols == 1:
            front_left_p = M - 1 - 2 * s
            front_right_p = -1
            back_left_p = 2 * s + 1
            back_right_p = -1
        else:
            front_left_p = M - 1 - 2 * s
            front_right_p = 2 * s
            back_left_p = 2 * s + 1
            back_right_p = M - 2 - 2 * s

        def build_side_grid(left_page_idx, right_page_idx):
            left_items = logical_pages[left_page_idx] if (0 <= left_page_idx < M) else []
            right_items = logical_pages[right_page_idx] if (0 <= right_page_idx < M) else []

            grid = []
            combined_items = []

            if cols == 1:
                for r in range(rows):
                    row_items = []
                    item = left_items[r] if r < len(left_items) else None
                    row_items.append(item)
                    combined_items.append(item)
                    grid.append(row_items)
            else:
                for r in range(rows):
                    row_items = []
                    # Left page columns
                    for c in range(left_cols):
                        idx = r * left_cols + c
                        item = left_items[idx] if idx < len(left_items) else None
                        row_items.append(item)
                        combined_items.append(item)
                    # Right page columns
                    for c in range(right_cols):
                        idx = r * right_cols + c
                        item = right_items[idx] if idx < len(right_items) else None
                        row_items.append(item)
                        combined_items.append(item)
                    grid.append(row_items)
            return combined_items, grid

        front_items, front_grid = build_side_grid(front_left_p, front_right_p)
        back_items, back_grid = build_side_grid(back_left_p, back_right_p)

        sheets.append({
            'sheet_index': s,
            'sheet_number': s + 1,
            'front': {
                'side': 'front',
                'logical_page_left': front_left_p + 1 if front_left_p >= 0 else None,
                'logical_page_right': front_right_p + 1 if front_right_p >= 0 else None,
                'logical_page_number': f"P{front_left_p + 1} | P{front_right_p + 1}" if cols > 1 else f"P{front_left_p + 1}",
                'items': front_items,
                'grid': front_grid,
                'rotate_180': False
            },
            'back': {
                'side': 'back',
                'logical_page_left': back_left_p + 1 if back_left_p >= 0 else None,
                'logical_page_right': back_right_p + 1 if back_right_p >= 0 else None,
                'logical_page_number': f"P{back_left_p + 1} | P{back_right_p + 1}" if cols > 1 else f"P{back_left_p + 1}",
                'items': back_items,
                'grid': back_grid,
                'rotate_180': rotate_back
            }
        })

    return {
        'total_images': total_images,
        'rows': rows,
        'cols': cols,
        'images_per_side': images_per_side,
        'images_per_sheet': images_per_sheet,
        'total_sheets': total_sheets,
        'total_logical_pages': total_logical_pages,
        'sheets': sheets
    }
