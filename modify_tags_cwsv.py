import os
import re
import pandas as pd


def ConvertChapterFiletoNuxeoCompatibleXML(chapter_file_path, statistics_df):

  print(chapter_file_path)
  with open(chapter_file_path, 'r') as f:
    content = f.read()
    i = content.find('<p class="center">')
    j = content.find('<h2>')
    print(i)
    print(j)

  ### Find which one appears first <p class  OR <h2>
  ## start with all text if both are not appearing

  if i == -1 and j == -1:
    pos = 0
  elif i == -1 and j > -1:
    pos = j
  elif i > -1 and j == -1:
    pos = i
  else:
    pos = min(i, j)

  print(pos)


  trim_content = content[pos:len(content)]

  #ftnote_count = trim_content.count('<a class="fnote"')
  #print('footnotes=' + str(ftnote_count))
  hyperlinks_count = trim_content.count('</a>')
  poem_count = trim_content.count('poem')
  LeftAlignedCounts = trim_content.count('<p class="center">')
  lists_count = trim_content.count('</li>')
  statistics_df = statistics_df.append(
    {'DocName': chapter_file_path, 'Hyperlinks Count (includes footnotes)': hyperlinks_count, 'PoemCounts': poem_count,
     'LeftAlignedCounts': LeftAlignedCounts, 'ListsCount': lists_count},
    ignore_index=True)

  # Vishesh: Unicode is not supported in Python 3
  trim_content = str(trim_content)

  # Vishesh: Remove newlines from the text and replace with a single space
  trim_content = trim_content.replace('\n', ' ')


  # Vishesh: Poems are to be treated differently. So do the needful

  start_poem = trim_content.find('<p class="poem" lang="sa">')
  while start_poem >= 0:
    end_poem = trim_content.find('</p>', start_poem) + len('</p>')
    print("Start Poem: %d, End Poem: %d" % (start_poem, end_poem))
    before_poem = trim_content[:start_poem]
    poem = trim_content[start_poem: end_poem + 1]
    print("Poem Before: " + poem)
    after_poem = trim_content[end_poem + 1:]
    poem = poem.replace('<p class="poem" lang="sa">',
                        '\n<Paragraph>\n<Poem>\n<PoemLanguage>HINDI</PoemLanguage>\n<PoemLine>')
    poem = poem.replace('<br>', '</PoemLine>\n<PoemLine>')
    poem = poem.replace('</p>', '</PoemLine>\n</Poem>\n</Paragraph>\n')
    print("Poem after: ", poem)

    trim_content = before_poem + poem + after_poem
    start_poem = trim_content.find('<p class="poem" lang="sa">')

  ### Replace texts

  trim_content = trim_content.replace('<p>', '\n<Paragraph>\n<Content>')

  trim_content = trim_content.replace('</p>', '</Content>\n</Paragraph>\n')

  trim_content = trim_content.replace('<h2>', '<ChapterTitle>')
  trim_content = trim_content.replace('</h2>', '</ChapterTitle>')

  trim_content = re.sub('<!--[^>]+-->', ' ', trim_content)
  trim_content = trim_content.replace('</div>', '')
  trim_content = trim_content.replace('</body></html>', '')

  trim_content = trim_content.replace('<br>', '')
  trim_content = trim_content.replace('<i>', '')
  trim_content = trim_content.replace('</i>', '')
  trim_content = trim_content.replace('&nbsp', ' ')
  trim_content = trim_content.replace('â', '&#226;')

  ### Replace <p class = Centre by Left aligned content

  start1 = '<p class="center">'
  end1 = '</Content>\n</Paragraph>\n'
  start2 = '\n<Paragraph>\n<LeftAlignedContent>'
  end2 = '</LeftAlignedContent>\n</Paragraph>\n'

  CenteredTexts = re.findall(r'\<p class="center">(.*?)\</Content>\n</Paragraph>\n', trim_content, re.DOTALL)
  len(CenteredTexts)
  t = 0
  Finds = []
  Replaces = []
  for text in CenteredTexts:
    print(text)
    textFind = start1 + text + end1
    Finds.append(textFind)
    print(textFind)
    textReplace = start2 + text + end2
    Replaces.append(textReplace)
    print(textReplace)
    t = t + 1
  print('list of texts to be found')
  print(Finds)
  print('list of texts to be replaced')
  print(Replaces)
  dictionary_find_replace = dict(zip(Finds, Replaces))
  print('\nDictonary\n')
  print(dictionary_find_replace)

  def replace_all(text, dic):
    for i, j in iter(dic.items()):
      text = text.replace(i, j)
    return text

  trim_content = replace_all(trim_content, dictionary_find_replace)
  trim_content = "\n<Chapter>" + trim_content + "\n</Chapter>"

  return trim_content, statistics_df


def convert_book_dir_to_nuxeo_compatible_xml(volume_number, book_name, book_dir_path, out_dir_path):
  '''
  Converts a dir containing each chapter of the book as a separate .htm file into a single consolidated XML. Note that
  chapters should be numbered to ensure the correct ordering of chapter texts within the produced xml file.
  :param volume_number: Volume Number
  :param book_name: Name of the book
  :param book_dir_path: The full directory path of the book
  :param out_dir_path: The dir where the produced XML file should be placed
  :return: None. Writes to a file
  '''
  chapter_files = [f for f in os.listdir(book_dir_path) if f.endswith('.htm')]
  chapter_files = sorted(chapter_files)

  len(chapter_files)
  print(chapter_files)
  statistics_df = pd.DataFrame()
  out_file_path = os.path.join(out_dir_path, book_name + '.xml')
  f = open(out_file_path, 'w')
  f.write('<Book>\n')
  f.write('<BookTitle>' + book_name + '</BookTitle>\n')
  f.write('<Language>ENGLISH</Language>\n')
  f.write('<BookId>Complete Works/Vivekananda/Volume ' + volume_number + '/' + book_name + '</BookId>\n')

  for chapter_file in chapter_files:
    chapter_file_path = os.path.join(book_dir_path, chapter_file)
    chapter_xml, statistics_df = ConvertChapterFiletoNuxeoCompatibleXML(chapter_file_path, statistics_df)
    f.write(chapter_xml)
  f.write('</Book>')
  f.close()
  print(statistics_df)
  statistics_df.to_csv(os.path.join(out_dir_path, 'Stats - ' + book_name + '.csv'), index=True, header=True)

def convert_volume_dir_to_nuxeo_compatible_xmls(volume_number, volume_dir_path, output_path):
  '''
    Converts a dir containing each book as a separate dir - each such dir named as the name of the book and containing
    each chapter as a separate .html file - into one consolidated XML per book.
    :param volume_number: Volume Number
    :param volume_dir_path: The full directory path of the volume
    :param output_path: The dir where the produced xml files should be placed
    :return: None. Creates and writes one file per book directory at the specified output_path
  '''
  book_dirs = [f for f in os.listdir(volume_dir_path) if os.path.isdir(os.path.join(volume_dir_path, f))]
  book_dirs = sorted(book_dirs)
  print('book_dirs:', book_dirs)
  for book_dir_name in book_dirs:
    # Remove seq number from book name. +2 is to remove '.' and space both
    dot_location = book_dir_name.find('.')
    if dot_location > 0:
      book_name = book_dir_name[dot_location+2:]
    else:
      book_name = book_dir_name
    book_dir_path = os.path.join(volume_dir_path, book_dir_name)
    convert_book_dir_to_nuxeo_compatible_xml(volume_number, book_name, book_dir_path, output_path)

def main():
  convert_volume_dir_to_nuxeo_compatible_xmls('1', 'C:\\Users\\gargvish\\SRCM\\NUXEO\\COLLATERALS\\BOOKS\\CWSV\\VOL1', 'C:\\Users\\gargvish\\SRCM\\NUXEO\\COLLATERALS\\BOOKS\\CWSV\\VOL1_OUTPUT')


if __name__ == "__main__":
  main()
