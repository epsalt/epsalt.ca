#!/usr/bin/env python

"""
Static site generator for epsalt.ca. Converts markdown documents to
html using markdown and jinja2. Generates archive and tag pages.
"""

import re
from collections import defaultdict
from os import listdir, makedirs
from os.path import exists, join

from dateutil.parser import parse
from markdown import Markdown
from jinja2 import FileSystemLoader, Environment
import yaml

POST_DIR = 'posts'
TEMPLATE_DIR = 'templates'
SITE_DIR = 'site'

class Page(object):
    """Base class for static website page rendering"""

    def __init__(self, md_fname):
        md = Markdown(extensions=['markdown.extensions.extra',
                                  'markdown.extensions.meta',
                                  'markdown.extensions.smarty'],
                      output_format='html5')
        
        with open(md_fname, 'r') as md_file:
            self.html = md.convert(md_file.read())

        # Remove list wrapping from everything except actual lists
        self.meta = {key: value if key == "tags" else value[0]
                     for key, value in md.Meta.items()}

    def render(self, template, template_args, out=None):
        """Method for rendering Pages with markdown and jinja2"""

        # Build jinja template argument dict
        args = {'post': self,
                'content': self.html}
        for key, value in template_args.items():
            args[key] = value

        # Build path for html document unless overridden by 'out'
        if out is None:
            out = self.link
        outpath = join(SITE_DIR, out)

        # Create directory if necessary
        if not exists(join(SITE_DIR, self.directory)):
            makedirs(join(SITE_DIR, self.directory))

        # Use jinja to render template and save
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        text = env.get_template(template).render(args)
        with open(outpath, 'w') as outfile:
            outfile.write(text)


class RootPage(Page):
    """Class for pages in the root dir of the website, extends page"""
    def __init__(self, f):
        Page.__init__(self, f)
        self.directory = "./"
        if self.meta.get('url') is not None:
            self.link = self.meta.get('url') + ".html"


class Post(Page):
    """Class for blog posts, extends Page"""

    def __init__(self, f):
        Page.__init__(self, f)

        self.date = parse(self.meta.get('date'))
        self.directory = join(self.date.strftime('%Y'),
                              self.date.strftime('%m'))
        self.link = join(self.directory, self.meta.get('url')) + ".html"
        self.ppost = None
        self.npost = None

    def set_neighbours(self, posts):
        """
        Sets npost and ppost attributes.

        Given a list of Posts, this method sets the npost and ppost
        attributes. It is necessary that the post using this method
        be in the list, if it is not ValueError will be raised.

        """
        index = posts.index(self)

        # Check if the Post is last
        if index == 0:
            self.npost = None
        else:
            self.npost = posts[index-1]

        # Check if the post is first
        if index == len(posts)-1:
            self.ppost = None
        else:
            self.ppost = posts[index+1]


def publish():
    """
    Generate all static site pages.

    This function finds all of the following and renders them as
    html in the SITE_DIR:
    - The about.md and archive.md file in the root directory
    - All posts in POST_DIR
    - All post tag files
    """

    # Get blog posts from POST_DIR
    posts = [Post(join(POST_DIR, post)) for post in listdir(POST_DIR)]
    sorted_posts = sorted(posts, key=lambda x: x.date, reverse=True)

    # Add previous and next post attributes to Post Class
    for post in sorted_posts:
        post.set_neighbours(sorted_posts)

    # Jinja2 template arguments
    args = {'posts': sorted_posts}

    # Build tag dict and render tag pages
    makedirs(join(SITE_DIR, "tag"))
    tag_dict = defaultdict(list)
    for post in sorted_posts:
        for tag in post.meta.get('tags'):
            tag_dict[tag].append(post)

    for tag, posts in tag_dict.items():
        out = join("tag", tag) + ".html"
        tag_args = {'posts': sorted_posts,
                    'tag_posts': posts,
                    'tag': tag}
        RootPage('tag.md').render('tag.html', tag_args, out=out)

    # Render all blog posts
    for post in sorted_posts:
        post.render('post.html', args)

    # Render site root pages
    sorted_posts[0].render('post.html', args, out=join('index.html'))
    RootPage('about.md').render('about.html', args)
    RootPage('archive.md').render('archive.html', args)

    return(sorted_posts)

if __name__ == "__main__":
    publish()