from bs4 import BeautifulSoup
from ebooklib import epub
import re
from utils.const import (
        BOOKS_DIR
        )
from utils.database import (
    get_highlight_from_database,
)


def get_table_of_contents_from_epub(path: str):
    """"""
    book = epub.read_epub(path, {'ignore_ncx': True})
    if not book:
        raise FileNotFoundError("The book doesn't seem to exist?")
    return book.toc


def retrieve_clean_href(href: str):
    """OEBPS/xhtml/Odel_9781612197500_epub3_itr_r1.xhtml#point(/1/4/22/4:478)
    ->
    xhtml/Odel_9781612197500_epub3_itr_r1.xhtml"""
    if '#' not in href:
        return href
    else:
        pattern = r"(?:^OEBPS/)?(.+?)(?=#)"
        result = re.findall(pattern, href)
        return result[0] if result else None


def get_dict_of_href_and_title_from_toc(toc):
    all_refs = {}
    for elem in toc:
        if isinstance(elem, epub.Link):
            clean = retrieve_clean_href(elem.href)
            if clean:
                all_refs[clean] = elem.title
        elif isinstance(elem, tuple):
            if isinstance(elem[0], epub.Section):
                for sub_elem in elem[1]:
                    if isinstance(sub_elem, epub.Link):
                        clean = retrieve_clean_href(sub_elem.href)
                        if clean:
                            all_refs[clean] = sub_elem.title

    return all_refs


# retrieves the preceding chapter from the table of contents
def get_previous_chapter_from_section(section: str, toc: dict) -> str:
    sorted_toc_sections = sorted(list(toc.keys()) + [section])
    i = sorted_toc_sections.index(section)
    return sorted_toc_sections[i - 1]


def match_highlight_section_to_chapter(section: str, toc) -> str | None:
    href_title_dict = get_dict_of_href_and_title_from_toc(toc)
    # 24/08/08: for STRANGERS, the section needed the OEBPS
    if '#' in section:
        split_section = section.split('#')[0]
        if split_section in href_title_dict.keys():
            return href_title_dict[split_section]
    clean_section = retrieve_clean_href(section)
    if clean_section in href_title_dict.keys():
        return href_title_dict[clean_section]
    # 24/04/17: if the section is not in the TOC, we try to map
    # to the preceding chapter
    else:
        return href_title_dict[get_previous_chapter_from_section(clean_section, href_title_dict)]
