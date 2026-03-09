"""
DOCX Generator — Creates a professional Word document from the blog post.
Uses Node.js docx library via subprocess.
"""
import os, json, subprocess, tempfile

DOCX_JS = r"""
const { Document, Packer, Paragraph, TextRun, HeadingLevel,
        AlignmentType, ImageRun, BorderStyle } = require('docx');
const fs = require('fs');
const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

function parseSections(content) {
  const lines = content.split('\n');
  const result = []; let cur = null;
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (cur) result.push(cur);
      cur = { heading: line.replace('## ','').trim(), paras: [] };
    } else if (line.trim() && cur) {
      cur.paras.push(line.trim());
    } else if (line.trim() && !cur) {
      result.push({ heading: null, paras: [line.trim()] });
    }
  }
  if (cur) result.push(cur);
  return result;
}

const content = data.humanized_content || data.content || '';
const sections = parseSections(content);
const children = [];

// Cover: Title
children.push(new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 0, after: 240 },
  children: [new TextRun({ text: data.title, bold: true, size: 44, font: 'Georgia' })]
}));

// Meta strip
const metaLine = [data.category, data.tone, (data.word_count||'') + ' words', data.slug ? '/'+data.slug : ''].filter(Boolean).join('  ·  ');
children.push(new Paragraph({
  spacing: { after: 80 },
  children: [new TextRun({ text: metaLine, size: 16, color: 'AAAAAA', font: 'Arial' })]
}));

// Meta description
children.push(new Paragraph({
  spacing: { after: 80 },
  border: { left: { style: BorderStyle.SINGLE, size: 6, color: '4F8EF7', space: 8 } },
  indent: { left: 360 },
  children: [
    new TextRun({ text: 'SEO: ', bold: true, size: 18, color: '4F8EF7', font: 'Arial' }),
    new TextRun({ text: data.meta_description || '', size: 18, italics: true, color: '555555', font: 'Arial' })
  ]
}));

// Image
if (data.image_b64) {
  try {
    children.push(new Paragraph({
      spacing: { before: 240, after: 360 },
      children: [new ImageRun({ data: Buffer.from(data.image_b64,'base64'), transformation: { width: 594, height: 334 }, type: 'png' })]
    }));
  } catch(e) {}
}

// Blog sections
for (const s of sections) {
  if (s.heading) {
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 320, after: 120 },
      children: [new TextRun({ text: s.heading, bold: true, size: 28, font: 'Georgia' })]
    }));
  }
  for (const p of s.paras) {
    children.push(new Paragraph({
      spacing: { after: 160 },
      children: [new TextRun({ text: p, size: 22, font: 'Arial' })]
    }));
  }
}

// LinkedIn post
if (data.linkedin_post) {
  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 480, after: 120 },
    children: [new TextRun({ text: 'LinkedIn Post', bold: true, size: 28, font: 'Georgia', color: '0077B5' })]
  }));
  for (const line of data.linkedin_post.split('\n')) {
    children.push(new Paragraph({
      spacing: { after: 100 },
      border: line ? { left: { style: BorderStyle.SINGLE, size: 3, color: '0077B5', space: 8 } } : undefined,
      indent: line ? { left: 280 } : undefined,
      children: [new TextRun({ text: line, size: 20, font: 'Arial' })]
    }));
  }
}

// Tweet thread
if (data.tweet_thread && data.tweet_thread.length) {
  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text: 'Twitter / X Thread', bold: true, size: 28, font: 'Georgia', color: '1DA1F2' })]
  }));
  for (const t of data.tweet_thread) {
    children.push(new Paragraph({
      spacing: { after: 120 },
      border: { left: { style: BorderStyle.SINGLE, size: 4, color: '1DA1F2', space: 8 } },
      indent: { left: 280 },
      children: [new TextRun({ text: t, size: 20, font: 'Arial' })]
    }));
  }
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id:'Heading1', name:'Heading 1', basedOn:'Normal', next:'Normal', quickFormat:true,
        run:{ size:44, bold:true, font:'Georgia' },
        paragraph:{ spacing:{ before:0, after:240 }, outlineLevel:0 } },
      { id:'Heading2', name:'Heading 2', basedOn:'Normal', next:'Normal', quickFormat:true,
        run:{ size:28, bold:true, font:'Georgia' },
        paragraph:{ spacing:{ before:280, after:120 }, outlineLevel:1 } },
    ]
  },
  sections: [{
    properties: { page: { size:{ width:12240, height:15840 }, margin:{ top:1440, right:1440, bottom:1440, left:1440 } } },
    children
  }]
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[3], buf); console.log('OK'); })
  .catch(e => { console.error(e); process.exit(1); });
"""

def generate_docx(data: dict) -> bytes | None:
    try:
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            script = os.path.join(td, 'gen.js')
            data_f = os.path.join(td, 'data.json')
            out_f  = os.path.join(td, 'out.docx')

            with open(script, 'w') as f: f.write(DOCX_JS)

            export = {k:v for k,v in data.items() if k != 'image_b64'}
            export['image_b64'] = (data.get('image_b64') or '')[:500000]
            with open(data_f, 'w') as f: json.dump(export, f)

            subprocess.run(['npm','install','docx','--prefix',td,'--silent'],
                           capture_output=True, timeout=60)
            r = subprocess.run(['node', script, data_f, out_f],
                               capture_output=True, text=True, timeout=60,
                               env={**os.environ,'NODE_PATH': os.path.join(td,'node_modules')})
            if r.returncode != 0:
                print(f"[DOCX] {r.stderr}")
                return None
            if os.path.exists(out_f):
                return open(out_f,'rb').read()
    except Exception as e:
        print(f"[DOCX] {e}")
    return None
