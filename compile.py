import os
import webapp2
import jinja2
from datetime import datetime
from google.appengine.ext import ndb


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
template_loader = jinja2.FileSystemLoader(template_dir)
# setting autoescape, an in-built feature in jinja2 that will escape HTML text coming from my content.py
# text input. Through this I can make my website more secure and provide a better user experience.
template_env = jinja2.Environment(loader = template_loader, autoescape = True)


class Handler(webapp2.RequestHandler):
    """contains the basic methods for rendering the templates into html pages"""
    def write(self, *arguments, **kw_arguments):
        """writes the content to a webpage, default as text/html"""
        self.response.out.write(*arguments, **kw_arguments)

    def render_str(self, template, **kw_arguments):
        """loads the specified template and renders the text"""
        t = template_env.get_template(template)
        return t.render(kw_arguments)

    def render(self, template, **kw_arguments):
        """calls the write function on the specified template's rendered text"""
        self.write(self.render_str(template, **kw_arguments))


class FormPage(Handler):
    """creates the page with the empty forms, that prompt the visitor for input"""
    def get(self):
        topics = ["your thoughts about servers", "your thoughts about templates", "your thoughts about escaping and validation",
                "what did you find especially interesting", "was there something that made you smile?"]
        self.render('form_tem.html', topics = topics)


class UserPage(Handler):
    def get(self):
        # allows to access all the Page objects' parameters from the datastore
        query = Page.query().order(Page.post_date)
        # assigning variable names to the variables of the Page object
        for i in query:
            topics = i.topics
            content = i.content
            name = i.name
            date = i.date
            css = i.css
            smile = i.smile
        # calling the render function with the arguments to display the page
        self.render('page_tem.html', topics = topics, content = content, name = name,
            date = date, css = css, smile = smile)

    def post(self):
        # the code following here gets the value of a query parameter
        name = self.request.get("name")
        css = self.request.get("css")
        smile = self.request.get("smile")
        # inserts the current time as a timestamp when the page got created
        date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M') + " (UTC)"
        # these are the headings that will display above the user's content
        topics = ["A micro guide to Servers", "Templating HTML", "Escaping troubles through Escaping and Validation",
                "! this was very interesting !", "* this made me smile *"]
        # get_all collects all the values of the specified query parameter and unifies them into a list
        paragraphs = self.request.get_all("content")
        # the next lines including the loop create a dictionary mapping the topics as keys to the paragraphs as values
        content = {}
        # a cool way of iterating with a for loop with index! thanks to my 2nd reviewer :)
        for index, topic in enumerate(topics):
            content[topic] = paragraphs[index]
        # sets the blank value to False by default, then tests if the name field is filled only by blanks
        blank = False
        if name.isspace():
            # if it's only blanks, it renders the form page again displaying an error message
            blank = True
            self.render('form_tem.html', topics = topics, blank = blank)
        # if all the necessary values are present, and name is not blank, instantiate a Page object
        elif name and date and topics and content and css and smile:
            input_page = Page(name = name, date = date, topics = topics, content = content,
             css = css, smile = smile)
            # add it to the datastore
            input_page.put()
            # allow a bit of time for the database to update
            import time
            delay_time = .1
            time.sleep(delay_time)
            # go to the page created by the user
            self.redirect('/userpage')
        # if necessary values are missing, redirect to a page displaying an error message
        else:
            self.redirect('/error')


class Collection(Handler):
    """this page collects all individual entries from the different users and puts them on one page"""
    def get(self):
        # this retrieves my objects from the datastore and sorts them in descending order (-)
        pages = Page.query().order(-Page.post_date)
        # I pass this variable that is a collection of all the user pages (objects) to my template
        # there I can iterate over them and create the individual pages (cool!)
        self.render('collection_tem.html', pages = pages)


class ErrorHandler(Handler):
    """displays an error message if instantiating the object fails"""
    def get(self):
        self.render('error_tem.html')


class Page(ndb.Model):
    """this is the Class that defines an object that will contain all the information that the user provides
    and that I will store on google data store and further use to display the individual pages on /collection."""
    # first two arguments are a list and a dictionary, therefore I need to use a different property.
    # topics (which is a list) can be made by using the repeated property.
    # I also tried the suggestion with content (which is a dict), however this does not work (PickleProperty does).
    topics = ndb.StringProperty(repeated=True)
    content = ndb.PickleProperty()
    name = ndb.StringProperty()
    css = ndb.StringProperty()
    smile = ndb.StringProperty()
    date = ndb.StringProperty()
    # this adds a timestamp to the generated object, about when it was created and stored.
    post_date = ndb.DateTimeProperty(auto_now_add = True)


app = webapp2.WSGIApplication([
    ('/', FormPage),
    ('/userpage', UserPage),
    ('/collection', Collection),
    ('/error', ErrorHandler)
], debug=True)
# debug = True means it writes out the errors onto my page, in case some occur