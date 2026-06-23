# markdown分块
1.先按照标题分(每个非一级标题需要携带父标题，如下面样例所示)
例如：
```
# Java

Java 是一种面向对象编程语言，由 Sun 公司开发。

它具有跨平台能力。

## JVM

JVM（Java Virtual Machine）负责执行 Java 字节码。

它主要包括：

- 类加载器
- 运行时数据区
- 执行引擎

### GC

GC（Garbage Collection）负责自动回收垃圾对象。

GC 算法包括：

- Serial GC
- CMS
- G1
- ZGC

### JIT

JIT（Just In Time）编译器负责将热点代码编译成本地机器码。

## Spring

Spring 是 Java 最流行的开发框架之一。

核心思想包括：

- IOC
- AOP
```
拆分成:
chunk1:
```
# Java

Java 是一种面向对象编程语言，由 Sun 公司开发。

它具有跨平台能力。
```
chunk2:
```
#Java
## JVM

JVM（Java Virtual Machine）负责执行 Java 字节码。

它主要包括：

- 类加载器
- 运行时数据区
- 执行引擎
```
chunk3:
```
#Java
## JVM
### GC

GC（Garbage Collection）负责自动回收垃圾对象。

GC 算法包括：

- Serial GC
- CMS
- G1
- ZGC
```
.....

2.如果一个标题下面依旧过大，则按多个完整句子拆分 overlap:100
3.列表不要直接拆分
列表：
```
优点：

①

②

③
```
错误拆分：

```
Chunk1  
  
优点：  
  
①
```

```
Chunk2

②

③
```
正确拆分
```
chunk1
优点:
1.
```

```
chunk2
优点
2.
3.
```
4.代码块拆分
- 优先尝试整个代码块
- 如果过长就按类拆分
- 如果类过大就按方法拆分（标注是哪个类）
- 如果方法太大，就按if{}，try{},等中括号拆分（表明哪个方法，类）
# TXT

TXT没有结构。

只能自己恢复结构。

例如：

```
Java是一门语言。JVM负责运行Java。GC负责垃圾回收。Spring负责IOC。
```

不要：

```
500 Token
```

应该：

## 第一层：按空行

```
Paragraph
```

例如：

```
第一段第二段第三段
```

---

## 第二层：按句号

例如：

```
。？！；
```

中文：

```
。！？；
```

英文：

```
.!?;
```

例如：

```
Java是一门语言。
JVM负责运行Java。
```

可以组成：

```
Chunk1
Java是一门语言。
JVM负责运行Java。
```

---

## 第三层：Token

超过：

```
800 Token
```

再切。

---

## Overlap

例如：

```
Chunk1Java...
JVM...
GC...
```

Chunk2：

```
JVM...
GC...
Spring...
```

共享：

```
100 Token
```

# PDF

## 第一步：文件类型检测（Document Classification）

上传 PDF 后，不要立刻解析。

先判断它属于哪一种 PDF。

主要有三种：

### 第一种：文本 PDF（最好处理）

例如：

```
Word↓导出 PDF
```

里面实际上保存着真正的文字。

例如：

```
JavaJVMGC
```

这种直接解析即可。

---

### 第二种：扫描 PDF

例如：

```
纸质书↓扫描↓PDF
```

实际上每一页都是：

```
page1.jpgpage2.jpg
```

没有任何文本。

必须：

```
OCR↓文字
```

---

### 第三种：混合 PDF

很多企业文档都是：

```
文字+图片+扫描页+表格
```

这种需要：

```
文字直接解析图片 OCR最后合并
```

---

## 第二步：PDF解析（Parser）

推荐 Parser：

```
DoclingMinerUUnstructuredPyMuPDFpdfplumber
```

推荐顺序：

```
Docling>MinerU>PyMuPDF
```

不要：

```
PyPDF2
```

因为：

- 丢格式
- 不识别表格
- 不恢复标题
- Layout 很差

---

## 第三步：OCR（如果需要用xiaomi的mimo-v2.5，apikey已经在配置文件）

如果检测到：

```
扫描 PDF
```

流程：

```
PDF↓每页转图片↓OCR↓文字
```

OCR 推荐：

```
PaddleOCRMinerU OCRAzure OCRGoogle OCR
```

OCR 输出的不仅仅是文字。

还会输出：

```
文字坐标字体大小方向
```

例如：

```
{  "text":"JVM",  "x":120,  "y":85,  "fontSize":18}
```

这些信息后面恢复结构要用。

---

## 第四步：Layout（版面分析）

这是生产环境最重要的一步。

例如：

论文：

```
标题左栏      右栏左栏      右栏图片表格
```

如果没有 Layout：

解析出来：

```
左1右1左2右2
```

语义完全乱。

所以：

先做：

```
Layout Detection
```

识别：

```
Title
Heading
Paragraph
Table
Image
Footer
Header
Caption
Formula
```

每个区域都会变成：

```
一个 Block
```

例如：

```
Block1Title
```

```
Block2Paragraph
```

```
Block3Table
```

```
Block4Image
```

## 第五步：恢复文档结构（Structure Recovery）

有了 Layout。

开始恢复：

```
H1H2H3
```

例如：

字体：

```
24px加粗居中
```

恢复：

```
#Java
```

例如：

```
18px加粗
```

恢复：

```
##JVM
```

例如：

```
16px
```

恢复：

```
###GC
```

最后形成：

```
Java

├── JVM
│      ├── GC
│      └── JIT
└── Spring
```

这就是后面的 Chunk Tree。
## Structure Chunking（最重要）

终于开始 Chunk。

优先级：

```
Heading↓Paragraph↓List↓Table↓Sentence
```

不是：

```
Token
```

例如：

```
## JVM正文...正文...正文...
```

得到：

```
Chunk
```

整个 Heading。

---

### List

整个 List 一起。

例如：

```
优点：①②③
```

不要拆：

```
①
```

```
②
```

---

### Table

整个 Table 一起。

不要：

```
第一列
```

```
第二列
```

---

### 图片

图片 Caption 一起。

例如：

```
图5JVM结构
```

一起。

---

## 第八步：Token Chunking

如果：

```
JVM8000 Token
```

不能整个 Embedding。

开始：

```
800 TokenOverlap100
```

例如：

```
Chunk10~800
```

```
Chunk2700~1500
```

```
Chunk31400~2200
```

每一个 Chunk：

都保留：

```
Heading Path
```

例如：

```
Java↓JVM
```

而不是：

只有正文。

---

## 第九步：Metadata

生产环境一定保存 Metadata。

例如：

```
{  "doc_id":"uuid",  "page":12,  "chunk_index":15,  "heading_path":[      "Java",      "JVM",      "GC"  ],  "content_type":"paragraph",  "token_count":680,  "previous_chunk":14,  "next_chunk":16}
```

**无论是txt还是md、pdf都要保存元数据**
