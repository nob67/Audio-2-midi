import pytest
from imposition import calculate_imposition


def test_imposition_empty():
    res = calculate_imposition(0, rows=2, cols=2)
    assert res['total_images'] == 0
    assert res['total_sheets'] == 0
    assert res['sheets'] == []


def test_imposition_saddle_stitch_pairing():
    # 2 sheets with 2x2 grid = 16 slots total (8 logical pages)
    res = calculate_imposition(16, rows=2, cols=2, rotate_back=True)
    assert res['total_sheets'] == 2
    assert res['total_logical_pages'] == 8

    sheet0 = res['sheets'][0]
    front0 = sheet0['front']
    back0 = sheet0['back']

    assert front0['logical_page_left'] == 8
    assert front0['logical_page_right'] == 1
    assert front0['rotate_180'] is False

    assert back0['logical_page_left'] == 2
    assert back0['logical_page_right'] == 7
    assert back0['rotate_180'] is True


def test_imposition_no_image_loss():
    total_imgs = 16
    input_imgs = [f"img_{i}.png" for i in range(total_imgs)]
    res = calculate_imposition(input_imgs, rows=2, cols=2)

    extracted = []
    for sheet in res['sheets']:
        for side in ['front', 'back']:
            for row in sheet[side]['grid']:
                for item in row:
                    if item is not None:
                        extracted.append(item)

    assert len(extracted) == total_imgs
    assert sorted(extracted) == sorted(input_imgs)
