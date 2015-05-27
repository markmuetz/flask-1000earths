import os
import fnmatch
import shutil
import markdown

if __name__ == '__main__':
    shutil.rmtree('templates/site')
    matches = []
    for root, dirnames, filenames in os.walk('site'):
        for filename in fnmatch.filter(filenames, '*.md'):
            matches.append(os.path.join(root, filename))
    print(matches)

    for path in matches:
        filename = os.path.splitext(path)[0]
        if not os.path.exists(filename + 'html'):
            markdown.markdownFromFile(input=filename + '.md', output=filename + '.html')
        output_file = os.path.join('templates', filename + '.html')
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        shutil.copyfile(filename + '.html', output_file)
