import pandas as pd
import re
from IPython.display import display

# 読み込む json データの path
json_data_path = './jawiki-country.json'
# json を DataFrame として読み込む
country_dfs = pd.read_json(json_data_path, lines=True)
# display(country_dfs)


def extract_country(dfs:pd.DataFrame, country:str) -> str:
  """ データフレーム dfs から特定の coutry に関する記事だけ抽出する
  """
  df = dfs.query('title=="{}"'.format(country)) # type: pandas.DataFrame
  texts = df['text'] # type: pandas.Series
  # texts.values が 要素数1(クエリに引っかかった数)の numpy 配列
  # texts.values[0] : str
  return texts.values[0]


def extract_categories(article:str) -> list:
  """ 与えられた記事からカテゴリ名を抽出して list にして返す
  """
  categories = re.findall(r'\[\[Category:(.+?)(?:\|.+?)?\]\]', article)
  return categories


def extract_sections(article:str, view=True) -> list:
  """ 与えられた記事からセクション構造を抽出し，セクション名とそのレベル(今回はh1,h2,h3の3つの見出しとする)を touple にした list を返す 
  """
  # touple (2つ以上の=, セクション名)の list が得られる
  sections = re.findall(r'(={2,})\s*(.+?)\s*\1', article)
  # '=' の数に応じてセクションのレベルを取得
  sections = [(len(sec[0])-1, sec[1]) for sec in sections]
  # view=Trueの時だけセクション構造を出力
  if view:
    for sec in sections:
      print('{indent}h{level} {section}'.format(indent='\t'*sec[0], level=sec[0], section=sec[1]))
  return sections


def extract_files(article:str) -> list:
  """ 与えられた記事から参照されているメディアファイルを全て抜き出して list にして返す
  """
  files = re.findall(r'\[\[ファイル:(.+?)(?:\|.+)?\]\]', article)
  return files


def extract_main_info(article:str) -> dict:
  """ 与えられた記事から「基本情報」テンプレートのフィールド名と値を取り出し，dict にして返す
  """
  # 基本情報の記述部分だけ抜き出し
  domain = re.findall(r'{{基礎情報 国((?:.|\n)+?)}}\n\n', article) # => 要素数1の list が返ってくる
  # list でなく str として取り出す
  domain = domain[0]
  
  # フィールド名とその値を取り出す
  fields_ = re.findall(r'^\|(.+?)\s*=\s*((?:.|\n[^\|])+)', domain, flags=re.MULTILINE) # => 要素数2の touple の list が返ってくる
  
  # fields_ を dict 型に変換する
  fields = dict()
  for f in fields_:
    fields[f[0]] = f[1]
  
  return fields


def dict2df(dic:dict) -> pd.DataFrame:
  """ 与えられた dict 型変数を pandas.DataFrame 型に変換して返す
  """
  df = pd.DataFrame([dic]) # 列名がkey, 各列の値が対応するvalになる
  return df.T #行と列入れ替えた方が見やすいので


def remove_strong(dic:dict) -> dict:
  """ 与えられた基本情報の辞書データに対して，強調マークアップを除去したものを返す
  """
  dic_ = dict() # この辞書を return する(引数のdicは破壊しない)
  for key, val in dic.items():
    strong_removed = re.sub(r"('{2,5})(.+?)\1", r'\2', val)
    dic_[key] = strong_removed
  return dic_


def remove_inlink(dic:dict) -> dict:
  """ 与えられた基本情報の辞書データに対して，内部リンクを除去したものを返す
  """
  dic_ = dict()
  for key, val in dic.items():
    inlink_removed = re.sub(r'\[\[(?:[^\]]+?\|)?(.+?)\]\]', r'\1', val)
    dic_[key] = inlink_removed
  return dic_

def remove_markups(dic:dict) -> dict:
  """与えられた基本情報の辞書データに対して，強調マークアップと内部リンク以外のいくつかのマークアップ記号を除去/一部抽出したものを返す．除去/抽出するマークアップの記号は以下．
  1. タグの除去
  2. 言語情報の抽出
  3. 仮リンクからの名前の抽出
  4. 言語情報と仮リンク以外の，{{}}で囲まれたテンプレートを除去
  5. http(s)リンクの除去
  """
  # 正規表現のルールと置き換え文字をまとめて定義してしまう
  rules = [
    r'<(.+?)>',                        # タグの除去
    r'\{\{lang\|(?:.+?)\|(.+?)}\}',    # 言語情報の抽出
    r'\{\{仮リンク\|(.+?)\|(?:.+?)}\}', # 仮リンクからの名前の抽出
    r'\{\{.+?\}\}',                    # 言語情報と仮リンク以外の，{{}}で囲まれたテンプレートを除去
    r'\[http.+?\]'                     # http(s)リンクの除去
    ]
  replacers = [
    '',
    r'\1',
    r'\1',
    '',
    ''
  ]

  # 各マークアップについて繰り返す
  for rule, replacer in zip(rules, replacers):
    for key, val in dic.items():
      markups_removed = re.sub(rule, replacer, val)
      dic[key] = markups_removed # 上2つの関数と異なり，引数の dict を破壊する
  return dic