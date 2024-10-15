import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from inscriptis import get_text
from minify_html import minify

from processing.tools.tools import dumb_find_text, dumb_get_text


def get_processed_text(  # noqa: C901
    page_source: str,
    base_url: str,
    html_parser: str = "lxml",
    keep_images: bool = True,
    remove_svg_image: bool = True,
    remove_gif_image: bool = True,
    remove_image_types: list = [],
    keep_webpage_links: bool = True,
    remove_script_tag: bool = True,
    remove_style_tag: bool = True,
    remove_tags: list = [],
    job_board_url="",
    important_words=[],
) -> str:
    """
    process html text. This helps the LLM to easily extract/scrape data especially image links and web links.
    modified https://github.com/m92vyas/llm-reader/blob/main/src/url_to_llm_text/get_llm_input_text.py

    Args:
      page_source (str): html source text
      base_url (str): url of the html source.
      html_parser (str): which beautifulsoup html parser to use, defaults to 'lxml'
      keep_images (bool): keep image links.
      remove_svg_image (bool): remove .svg image. usually not useful while scraping. default True
      remove_gif_image (bool): remove .gif image. usually not useful while scraping. default True
      remove_image_types (list): add any image extensions which you want to remove inside a list. eg: [.png].
      keep_webpage_links (bool): keep webpage links.
      remove_script_tag (bool): True
      remove_style_tag (bool): =True
      remove_tags (list): = list of tags to be remove. Default []

    Returns (str):
      LLM ready input web page text
    """

    try:
        soup = BeautifulSoup(page_source, html_parser)

        # -------remove tags----------
        remove_tag = []
        if remove_script_tag:
            remove_tag.append("script")
        if remove_style_tag:
            remove_tag.append("style")
        remove_tag.extend(remove_tags)
        remove_tag = list(set(remove_tag))
        important_context = []
        for tag in soup.find_all(remove_tag):
            if job_board_url:
                important_context.extend(dumb_find_text(str(tag), context_len=50, main_url=job_board_url))
            try:
                tag.extract()
            except Exception as e:
                logging.error(f"Error while removing tag({tag}): {e}")
                continue

        # --------process image links--------
        remove_image_type = []
        if remove_svg_image:
            remove_image_type.append(".svg")
        if remove_gif_image:
            remove_image_type.append(".gif")
        remove_image_type.extend(remove_image_types)
        remove_image_type = list(set(remove_image_type))
        images = soup.find_all("img")
        for image in images:
            try:
                if not keep_images:
                    image.replace_with("")
                else:
                    image_link = image.get("src")
                    type_replaced = False
                    if isinstance(image_link, str):
                        if remove_image_type != []:
                            for image_type in remove_image_type:
                                if not type_replaced and image_type in image_link:
                                    image.replace_with("")
                                    type_replaced = True
                        if not type_replaced:
                            image.replace_with("\n" + urljoin(base_url, image_link) + " ")
            except Exception as e:
                logging.error(f"Error while getting image link({image_link}): {e}")
                continue
        # ----------process website links-----------
        urls = soup.find_all("a", href=True)
        for link in urls:
            try:
                if not keep_webpage_links:
                    link.replace_with("")
                else:
                    link.replace_with(link.text + ": " + urljoin(base_url, link["href"]) + " ")
            except Exception as e:
                logging.error(f"Error while getting webpage link: {e}")
                continue

        # -----------change text structure-----------
        def find_important_words(important_words, text):
            if important_words:
                pattern = re.compile(r"(" + "|".join(important_words) + r")", re.IGNORECASE)

                # Find all matches and their positions
                matches = pattern.finditer(text)
                return any(matches)
            else:
                return False

        def track_important_words(important_words, text, new_text):
            important_word_status = find_important_words(important_words, text)
            new_important_word_status = find_important_words(important_words, new_text)
            if new_important_word_status != important_word_status:
                return dumb_find_text(text, context_len=50)
            else:
                return []

        for element in soup.find_all(True):  # Find all elements
            try:
                if "search-filter" in (element.get("id", "") + " " + " ".join(element.get("class", []))):
                    element.decompose()
            except Exception:
                pass
        body_content = soup.find("body")

        important_context.extend(
            track_important_words(
                important_words=important_words,
                text=str(soup),
                new_text=str(body_content),
            )
        )
        if body_content:
            try:
                minimized_body = minify(str(body_content))
                important_context.extend(
                    track_important_words(
                        important_words=important_words,
                        text=str(body_content),
                        new_text=str(minimized_body),
                    )
                )
                text = get_text(minimized_body)
                important_context.extend(
                    track_important_words(
                        important_words=important_words,
                        text=str(minimized_body),
                        new_text=str(text),
                    )
                )
                if text == "":
                    text = dumb_get_text(str(minimized_body))
                    if text == "":
                        text = dumb_get_text(str(body_content))
            except Exception:
                text = get_text(str(body_content))
                if text == "":
                    text = dumb_get_text(str(body_content))
        else:
            text = soup.get_text()
        if text == "":
            text = dumb_get_text(str(soup))
        text = text + "\n\n".join(important_context)
        return text

    except Exception as e:
        logging.error(f"get_processed_text error. Base_url: {base_url}, job_board_url: {job_board_url}, error: {e}")
        return ""
