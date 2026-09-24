import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from 图片随机测试 import discover_images, choose_test_items, load_display_image  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    folder = Path(d)
    Image.new('RGB', (1600, 900), 'white').save(folder / '001_苹果.png')
    Image.new('RGB', (300, 1200), 'white').save(folder / '人物（张三）.jpg')
    Image.new('RGB', (500, 500), 'white').save(folder / 'A B_(测试).webp')
    (folder / 'bad.jpg').write_bytes(b'not an image')
    (folder / '说明.txt').write_text('ignored', encoding='utf-8')
    (folder / '子目录').mkdir()
    Image.new('RGB', (10, 10), 'white').save(folder / '子目录' / 'nested.png')

    items = discover_images(folder)
    assert len(items) == 4
    assert {i.answer for i in items} == {'001_苹果', '人物（张三）', 'A B_(测试)', 'bad'}
    selected = choose_test_items(items, 3)
    assert len(selected) == 3 and len({i.path for i in selected}) == 3
    assert load_display_image(folder / '001_苹果.png', 800, 600).size == (800, 450)
    assert load_display_image(folder / '人物（张三）.jpg', 800, 600).size == (150, 600)
    try:
        choose_test_items(items, 5)
    except ValueError:
        pass
    else:
        raise AssertionError('count overflow should raise ValueError')

print('所有非 GUI 自测通过。')
