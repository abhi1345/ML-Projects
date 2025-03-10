
# coding: utf-8

# # Project 3 - Classification
# Welcome to the third project of Data 8!  You will build a classifier that guesses whether a movie is romance or action, using only the numbers of times words appear in the movies's screenplay.  By the end of the project, you should know how to:
# 
# 1. Build a k-nearest-neighbors classifier.
# 2. Test a classifier on data.
# 
# ### Logistics
# 
# 
# **Deadline.** This project is due at 11:59pm on Friday 4/27. You can earn an early submission bonus point by submitting your completed project by Thursday 4/26. It's **much** better to be early than late, so start working now.
# 
# **Checkpoint.** For full credit, you must also **complete Part 1 of the project (out of 4) and submit it by 11:59pm on Friday 4/20**. You will have some lab time to work on these questions, but we recommend that you start the project before lab and leave time to finish the checkpoint afterward.
# 
# **Partners.** You may work with one other partner; this partner **must** be enrolled in the same lab section as you are. Only one of you is required to submit the project. On [okpy.org](http://okpy.org), the person who submits should also designate their partner so that both of you receive credit.
# 
# **Rules.** Don't share your code with anybody but your partner. You are welcome to discuss questions with other students, but don't share the answers. The experience of solving the problems in this project will prepare you for exams (and life). If someone asks you for the answer, resist! Instead, you can demonstrate how you would solve a similar problem.
# 
# **Support.** You are not alone! Come to office hours, post on Piazza, and talk to your classmates. If you want to ask about the details of your solution to a problem, make a private Piazza post and the staff will respond. If you're ever feeling overwhelmed or don't know how to make progress, email your TA or tutor for help. You can find contact information for the staff on the [course website](http://data8.org/sp18/staff.html).
# 
# **Tests.** Passing the tests for a question **does not** mean that you answered the question correctly. Tests usually only check that your table has the correct column labels. However, more tests will be applied to verify the correctness of your submission in order to assign your final score, so be careful and check your work!
# 
# **Advice.** Develop your answers incrementally. To perform a complicated table manipulation, break it up into steps, perform each step on a different line, give a new name to each result, and check that each intermediate result is what you expect. You can add any additional names or functions you want to the provided cells. Also, please be sure to not re-assign variables throughout the notebook! For example, if you use max_temperature in your answer to one question, do not reassign it later on.
# 
# To get started, load `datascience`, `numpy`, `plots`, and `ok`.

# In[1]:


# Run this cell to set up the notebook, but please don't change it.

import numpy as np
import math
from datascience import *

# These lines set up the plotting functionality and formatting.
import matplotlib
matplotlib.use('Agg', warn=False)
get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plots
plots.style.use('fivethirtyeight')
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# These lines load the tests.
from client.api.notebook import Notebook
ok = Notebook('project3.ok')
_ = ok.auth(inline=True)


# # 1. The Dataset
# 
# In this project, we are exploring movie screenplays. We'll be trying to predict each movie's genre from the text of its screenplay. In particular, we have compiled a list of 5,000 words that might occur in the dialog of a movie. For each movie, our dataset tells us the frequency with which each of these words occurs in its screenplay. All words have been converted to lowercase.
# 
# Run the cell below to read the `movies` table. **It may take up to a minute to load.**

# In[2]:


movies = Table.read_table('movies.csv')
movies.where("Title", "the matrix").select(0, 1, 2, 3, 4, 5, 10, 30, 5005)


# The above cell prints a few columns of the row for the action movie *The Matrix*.  The movie contains 3792 words. The word "it" appears 115 times, as it makes up  $\frac{115}{3792} \approx 0.030327$ of the words in the movie. The word "not" appears 33 times, as it makes up $\frac{33}{3792} \approx 0.00870253$ of the words. The word "fling" doesn't appear at all.
# 
# This numerical representation of a body of text, one that describes only the frequencies of individual words, is called a bag-of-words representation. A lot of information is discarded in this representation: the order of the words, the context of each word, who said what, the cast of characters and actors, etc. However, a bag-of-words representation is often used for machine learning applications as a reasonable starting point, because a great deal of information is also retained and expressed in a convenient and compact format. In this project, we will investigate whether this representation is sufficient to build an accurate genre classifier.

# All movie titles are unique. The `row_for_title` function provides fast access to the one row for each title. 

# In[3]:


title_index = movies.index_by('Title')
def row_for_title(title):
    """Return the row for a title, similar to the following expression (but faster)
    
    movies.where('Title', title).row(0)
    """
    return title_index.get(title)[0]


# For example, the fastest way to find the frequency of "hey" in the movie *The Terminator* is to access the `'hey'` item from its row. Check the original table to see if this worked for you!

# In[4]:


row_for_title('the terminator').item('hey') 


# #### Question 1.1
# Set `expected_row_sum` to the number that you __expect__ will result from summing all proportions in each row, excluding the first six columns.

# In[5]:


# Set row_sum to a number that's the (approximate) sum of each row of word proportions.
expected_row_sum = 1


# In[6]:


_ = ok.grade("q1_1")
_ = ok.backup()


# This dataset was extracted from [a Kaggle dataset from Cornell University](https://www.kaggle.com/Cornell-University/movie-dialog-corpus). After transforming the dataset (e.g., converting the words to lowercase, removing the naughty words, and converting the counts to frequencies), we created this new dataset containing the frequency of 5000 common words in each movie.

# In[7]:


print('Words with frequencies:', movies.drop(np.arange(6)).num_columns) 
print('Movies with genres:', movies.num_rows)


# ## 1.1. Word Stemming
# The columns other than "Title", "Genre", "Year", "Rating", "# Votes" and "# Words" in the `movies` table are all words that appear in some of the movies in our dataset.  These words have been *stemmed*, or abbreviated heuristically, in an attempt to make different [inflected](https://en.wikipedia.org/wiki/Inflection) forms of the same base word into the same string.  For example, the column "manag" is the sum of proportions of the words "manage", "manager", "managed", and "managerial" (and perhaps others) in each movie.  
# 
# Stemming makes it a little tricky to search for the words you want to use, so we have provided another table that will let you see examples of unstemmed versions of each stemmed word.  Run the code below to load it.

# In[8]:


# Just run this cell.
vocab_mapping = Table.read_table('stem.csv')
stemmed = np.take(movies.labels, np.arange(3, len(movies.labels)))
vocab_table = Table().with_column('Stem', stemmed).join('Stem', vocab_mapping)
vocab_table.take(np.arange(1100, 1110))


# #### Question 1.1.1
# Assign `stemmed_message` to the stemmed version of the word "alternating".

# In[9]:


# Set stemmed_message to the stemmed version of "alternating" (which
# should be a string).  Use vocab_table.
stemmed_message = vocab_table.where('Word', 'alternating').column('Stem').item(0)
stemmed_message


# In[10]:


_ = ok.grade("q1_1_1")
_ = ok.backup()


# #### Question 1.1.2
# Assign `unstemmed_run` to an array of words in `vocab_table` that have "run" as its stemmed form. 

# In[11]:


# Set unstemmed_run to the unstemmed versions of "run" (which
# should be an array of string).
unstemmed_run = vocab_table.where('Stem', 'run').column('Word')
unstemmed_run


# In[12]:


_ = ok.grade("q1_1_2")
_ = ok.backup()


# #### Question 1.1.3
# Assign `percent_unchanged` to the **percentage** of words in `vocab_table` that are the same as their stemmed form (such as "blame" above).

# In[13]:


testtable = vocab_table.with_columns('1', vocab_table.apply(len, 'Word'), 
                                        '2', vocab_table.apply(len, 'Stem'))

testtable = testtable.with_column('change', testtable.column('1') - testtable.column('2'))

num_unchanged = testtable.where('change', 0).num_rows
percent_unchanged = 100 * num_unchanged / (vocab_table.num_rows)
print(round(percent_unchanged, 2), '% are unchanged')


# In[14]:


_ = ok.grade("q1_1_3")
_ = ok.backup()


# #### Question 1.1.4
# Which word in `vocab_table` was shortened the most by this stemming process? Assign `most_shortened` to the word. If there are multiple words, use the word whose first letter is earliest in the alphabet (so if your options are albatross or batman, you should pick albatross). 
# 
# It's an example of how heuristic stemming can collapse two unrelated words into the same stem (which is bad, but happens a lot in practice anyway).

# In[15]:


# In our solution, we found it useful to first make an array
# containing the number of characters that was
# chopped off of each word in vocab_table, but you don't have
# to do that.

most_shortened = testtable.where('change', max(testtable.column('change'))).column('Word').item(0)

# This will display your answer and its shortened form.
vocab_table.where('Word', most_shortened)


# In[16]:


_ = ok.grade("q1_1_4")
_ = ok.backup()


# ## 1.2. Splitting the dataset
# We're going to use our `movies` dataset for two purposes.
# 
# 1. First, we want to *train* movie genre classifiers.
# 2. Second, we want to *test* the performance of our classifiers.
# 
# Hence, we need two different datasets: *training* and *test*.
# 
# The purpose of a classifier is to classify unseen data that is similar to the training data. Therefore, we must ensure that there are no movies that appear in both sets. We do so by splitting the dataset randomly. The dataset has already been permuted randomly, so it's easy to split.  We just take the top for training and the rest for test. 
# 
# Run the code below (without changing it) to separate the datasets into two tables.

# In[17]:


# Here we have defined the proportion of our data
# that we want to designate for training as 17/20ths
# of our total dataset.  3/20ths of the data is
# reserved for testing.

training_proportion = 17/20

num_movies = movies.num_rows
num_train = int(num_movies * training_proportion)
num_valid = num_movies - num_train

train_movies = movies.take(np.arange(num_train))
test_movies = movies.take(np.arange(num_train, num_movies))

print("Training: ",   train_movies.num_rows, ";",
      "Test: ",       test_movies.num_rows)


# #### Question 1.2.1
# Draw a horizontal bar chart with two bars that show the proportion of Romance movies in each dataset.  Complete the function `romance_proportion` first; it should help you create the bar chart.

# In[18]:


def romance_proportion(table):
    """Return the proportion of movies in a table that have the Romance genre."""
    return table.where('Genre', 'romance').num_rows / table.num_rows

# The staff solution took multiple lines.  Start by creating a table.
# If you get stuck, think about what sort of table you need for barh to work
Table().with_columns('Name', make_array('Train', 'Test'),
                    'Proportion', make_array(romance_proportion(train_movies),romance_proportion(test_movies))).barh('Name', 'Proportion')


# ### Checkpoint Reached
# 
# You have reached the project checkpoint. Please submit now in order to record your progress. If you go back and revise your answers in the section above after the checkpoint is due, that's fine. Your revised answers will be graded. However, you will only get credit for your checkpoint submission if you have passed the tests provided for every question above.
# 
# If you are working with a partner, only one of you needs to submit. For both of you to receive credit, the person who submits must invite the other to be their partner on [okpy.org](http://okpy.org). Please invite your partner now and tell them to accept the invitation **before** the checkpoint deadline!

# In[19]:


_ = ok.submit()


# # 2. K-Nearest Neighbors - A Guided Example
# 
# K-Nearest Neighbors (k-NN) is a classification algorithm.  Given some *attributes* (also called *features*) of an unseen example, it decides whether that example belongs to one or the other of two categories based on its similarity to previously seen examples. Predicting the category of an example is called *labeling*, and the predicted category is also called a *label*.
# 
# An attribute (feature) we have about each movie is *the proportion of times a particular word appears in the movies*, and the labels are two movie genres: romance and action.  The algorithm requires many previously seen examples for which both the attributes and labels are known: that's the `train_movies` table.
# 
# To build understanding, we're going to visualize the algorithm instead of just describing it.

# ## 2.1. Classifying a movie
# 
# In k-NN, we classify a movie by finding the `k` movies in the *training set* that are most similar according to the features we choose. We call those movies with similar features the *nearest neighbors*.  The k-NN algorithm assigns the movie to the most common category among its `k` nearest neighbors.
# 
# Let's limit ourselves to just 2 features for now, so we can plot each movie.  The features we will use are the proportions of the words "money" and "feel" in the movie.  Taking the movie "Batman Returns" (in the test set), 0.000502 of its words are "money" and 0.004016 are "feel". This movie appears in the test set, so let's imagine that we don't yet know its genre.
# 
# First, we need to make our notion of similarity more precise.  We will say that the *distance* between two movies is the straight-line distance between them when we plot their features in a scatter diagram. This distance is called the Euclidean ("yoo-KLID-ee-un") distance, whose formula is $\sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$.
# 
# For example, in the movie *Titanic* (in the training set), 0.0009768 of all the words in the movie are "money" and 0.0017094 are "feel".  Its distance from *Batman Returns* on this 2-word feature set is $\sqrt{(0.000502 - 0.0009768)^2 + (0.004016 - 0.0017094)^2} \approx 0.00235496$.  (If we included more or different features, the distance could be different.)
# 
# A third movie, *The Avengers* (in the training set), is 0 "money" and 0.001115 "feel".
# 
# The function below creates a plot to display the "money" and "feel" features of a test movie and some training movies. As you can see in the result, *Batman Returns* is more similar to *Titanic* than to *The Avengers* based on these features. However, we know that *Batman Returns* and *The Avengers* are both action movies, so intuitively we'd expect them to be more similar. Unfortunately, that isn't always the case. We'll discuss this more later.

# In[20]:


# Just run this cell.
def plot_with_two_features(test_movie, training_movies, x_feature, y_feature):
    """Plot a test movie and training movies using two features."""
    test_row = row_for_title(test_movie)
    distances = Table().with_columns(
            x_feature, [test_row.item(x_feature)],
            y_feature, [test_row.item(y_feature)],
            'Color',   ['unknown'],
            'Title',   [test_movie]
        )
    for movie in training_movies:
        row = row_for_title(movie)
        distances.append([row.item(x_feature), row.item(y_feature), row.item('Genre'), movie])
    distances.scatter(x_feature, y_feature, colors='Color', labels='Title', s=30)
    
training = ["titanic", "the avengers"] 
plot_with_two_features("batman returns", training, "money", "feel")
plots.axis([-0.001, 0.0015, -0.001, 0.006])


# #### Question 2.1.1
# 
# Compute the distance between the two action movies, *Batman Returns* and *The Avengers*, using the `money` and `feel` features only.  Assign it the name `romance_distance`. (Edit: It would make more sense conceptually to call this 'action_distance', unfortunately, the test looks specifically for the name 'romance_distance'.)
# 
# **Note:** If you have a row object, you can use `item` to get a value from a column by its name.  For example, if `r` is a row, then `r.item("Genre")` is the value in column `"Genre"` in row `r`.
# 
# *Hint*: Remember the function `row_for_title`, redefined for you below. 

# In[21]:


title_index = movies.index_by('Title')
def row_for_title(title):
    """Return the row for a title, similar to the following expression (but faster)
    
    movies.where('Title', title).row(0)
    """
    return title_index.get(title)[0]


# In[22]:


batman = row_for_title("batman returns") 
avengers = row_for_title("the avengers") 
romance_distance = np.sqrt((batman.item("feel") - avengers.item("feel"))**2 + (batman.item("money") - avengers.item("money"))**2)
romance_distance


# In[23]:


_ = ok.grade("q2_1_1")
_ = ok.backup()


# Below, we've added a third training movie, *The Terminator*. Before, the point closest to *Batman Returns* was *Titanic*, a romance movie. However, now the closest point is *The Terminator*, an action movie.

# In[24]:


training = ["the avengers", "titanic", "the terminator"] 
plot_with_two_features("batman returns", training, "money", "feel") 
plots.axis([-0.001, 0.0015, -0.001, 0.006])


# #### Question 2.1.2
# Complete the function `distance_two_features` that computes the Euclidean distance between any two movies, using two features. The last two lines call your function to show that *Batman Returns* is closer to *The Terminator* than *The Avengers*. 

# In[25]:


def distance_two_features(title0, title1, x_feature, y_feature):
    """Compute the distance between two movies with titles title0 and title1
    
    Only the features named x_feature and y_feature are used when computing the distance.
    """
    row0 = row_for_title(title0)
    row1 = row_for_title(title1)
    return np.sqrt((row0.item(x_feature) - row1.item(x_feature))**2 + (row0.item(y_feature) - row1.item(y_feature))**2)


for movie in make_array("the terminator", "the avengers"):
    movie_distance = distance_two_features(movie, "batman returns", "money", "feel")
    print(movie, 'distance:\t', movie_distance)


# In[26]:


_ = ok.grade("q2_1_2")
_ = ok.backup()


# #### Question 2.1.3
# Define the function `distance_from_batman_returns` so that it works as described in its documentation. 

# In[27]:


def distance_from_batman_returns(title):
    """The distance between the given movie and "batman returns", based on the features "money" and "feel".
    
    This function takes a single argument:
      title: A string, the name of a movie.
    """
    
    return distance_two_features(title, "batman returns", "money", "feel")


# In[28]:


_ = ok.grade("q2_1_3")
_ = ok.backup()


# #### Question 2.1.4
# 
# Using the features `"money" and "feel"`, what are the names and genres of the 7 movies in the **training set** closest to "batman returns"?  To answer this question, make a table named `close_movies` containing those 7 movies with columns `"Title"`, `"Genre"`, `"money"`, and `"feel"`, as well as a column called `"distance"` that contains the distance from "batman returns".  The table should be **sorted in ascending order by `distance`**.

# In[29]:


# The staff solution took multiple lines.
sortedtable = train_movies
sortedtable = sortedtable.with_column("distance", sortedtable.apply(distance_from_batman_returns, "Title")).sort("distance")

close_movies = sortedtable.select("Title", "Genre", "money", "feel", "distance").take(np.arange(0,7))
close_movies


# In[30]:


_ = ok.grade("q2_1_4")
_ = ok.backup()


# #### Question 2.1.5
# Next, we'll clasify "batman returns" based on the genres of the closest movies. 
# 
# To do so, define the function `most_common` so that it works as described in its documentation below.

# In[31]:


def most_common(label, table):
    """The most common element in a column of a table.
    
    This function takes two arguments:
      label: The label of a column, a string.
      table: A table.
     
    It returns the most common value in that column of that table.
    In case of a tie, it returns any one of the most common values
    """
    col = table.column(label)
    a = col.item(0)
    for i in col:
        if np.count_nonzero(col == a) < np.count_nonzero(col == i):
            a = i
            
    return a

# Calling most_common on your table of 7 nearest neighbors classifies
# "batman returns" as a romance movie, 5 votes to 2. 
most_common('Genre', close_movies)


# In[32]:


_ = ok.grade("q2_1_5")
_ = ok.backup()


# Congratulations are in order -- you've classified your first movie! However, we can see that the classifier doesn't work too well since it categorized Batman Returns as a romance movie (unless you count the bromance between Alfred and Batman). Let's see if we can do better!

# # 3. Features

# Now, we're going to extend our classifier to consider more than two features at a time.
# 
# Euclidean distance still makes sense with more than two features. For `n` different features, we compute the difference between corresponding feature values for two movies, square each of the `n`  differences, sum up the resulting numbers, and take the square root of the sum.

# #### Question 3.1
# Write a function to compute the Euclidean distance between two **arrays** of features of *arbitrary* (but equal) length.  Use it to compute the distance between the first movie in the training set and the first movie in the test set, *using all of the features*.  (Remember that the first six columns of your tables are not features.)
# 
# **Note:** To convert row objects to arrays, use `np.array`. For example, if `t` was a table, `np.array(t.row(0))` converts row 0 of `t` into an array.

# In[33]:


def distance(features1, features2):
    """The Euclidean distance between two arrays of feature values."""
    tsum = 0
    index = 0
    while index < len(features1):
        tsum += (float(features1[index]) - float(features2[index]))**2
        index+=1
        
    return np.sqrt(tsum)

distance_first_to_first = distance(np.array(train_movies.row(1))[6:], np.array(test_movies.row(1))[6:])
distance_first_to_first


# In[34]:


_ = ok.grade("q3_1")
_ = ok.backup()


# ## 3.1. Creating your own feature set
# 
# Unfortunately, using all of the features has some downsides.  One clear downside is *computational* -- computing Euclidean distances just takes a long time when we have lots of features.  You might have noticed that in the last question!
# 
# So we're going to select just 20.  We'd like to choose features that are very *discriminative*. That is, features which lead us to correctly classify as much of the test set as possible.  This process of choosing features that will make a classifier work well is sometimes called *feature selection*, or more broadly *feature engineering*.

# #### Question 3.0.1
# In this question, we will help you get started on selecting more effective features for distinguishing romance from action movies. The plot below (generated for you) shows the average number of times each word occurs in a romance movie on the horizontal axis and the average number of times it occurs in an action movie on the vertical axis. 

# ![alt text](word_plot.png "Title")

# The following questions ask you to interpret the plot above. For each question, select one of the following choices and assign its number to the provided name.
#     1. The word is uncommon in both action and romance movies
#     2. The word is common in action movies and uncommon in romance movies
#     3. The word is uncommon in action movies and common in romance movies
#     4. The word is common in both action and romance movies
#     5. It is not possible to say from the plot 

# What properties does a word in the bottom left corner of the plot have? Your answer should be a single integer from 1 to 5, corresponding to the correct statement from the choices above.

# In[35]:


bottom_left = 1


# In[36]:


_ = ok.grade("q3_0_1")
_ = ok.backup()


# What properties does a word in the bottom right corner have?

# In[37]:


bottom_right = 3


# In[38]:


_ = ok.grade("q3_0_2")
_ = ok.backup()


# What properties does a word in the top right corner have?

# In[39]:


top_right = 4 


# In[40]:


_ = ok.grade("q3_0_3")
_ = ok.backup()


# What properties does a word in the top left corner have?

# In[41]:


top_left = 2 


# In[42]:


_ = ok.grade("q3_0_4")
_ = ok.backup()


# If we see a movie with a lot of words that are common for action movies but uncommon for romance movies, what would be a reasonable guess about the genre of the movie? 
#     1. It is an action movie.
#     2. It is a romance movie.

# In[43]:


movie_genre_guess = 1


# In[44]:


_ = ok.grade("q3_0_5")
_ = ok.backup()


# #### Question 3.1.1
# Using the plot above, choose 20 common words that you think might let you distinguish between romance and action movies. Make sure to choose words that are frequent enough that every movie contains at least one of them. Don't just choose the 20 most frequent, though... you can do much better.
# 
# You might want to come back to this question later to improve your list, once you've seen how to evaluate your classifier.  

# In[45]:


# Set my_20_features to an array of 20 features (strings that are column labels)

my_20_features = ['save', 'took', 'head', 'done', 'knew', 'hour', 'without', 'most', 'question', 'head',
                 'fine', 'boy', 'miss', 'home', 'marri', 'mother', 'huh', 'hous', 'hello', 'write']

train_20 = train_movies.select(my_20_features)
test_20 = test_movies.select(my_20_features)


# This test makes sure that you have chosen words such that at least one appears in each movie. If you can't find words that satisfy this test just through intuition, try writing code to print out the titles of movies that do not contain any words from your list, then look at the words they do contain.

# In[46]:


_ = ok.grade("q3_1_1")
_ = ok.backup()


# #### Question 3.1.2
# In two sentences or less, describe how you selected your features. 

# *I split this set into 2 types of words: those common in action movies but not romance, and vice versa. By this measure, the classifier will be able to classify movies based on words that are either common in action or in romance, but not both. *

# Next, let's classify the first movie from our test set using these features.  You can examine the movie by running the cells below. Do you think it will be classified correctly?

# In[47]:


print("Movie:")
test_movies.take(0).select('Title', 'Genre').show()
print("Features:")
test_20.take(0).show()


# As before, we want to look for the movies in the training set that are most alike our test movie.  We will calculate the Euclidean distances from the test movie (using the 20 selected features) to all movies in the training set.  You could do this with a `for` loop, but to make it computationally faster, we have provided a function, `fast_distances`, to do this for you.  Read its documentation to make sure you understand what it does.  (You don't need to read the code in its body unless you want to.)

# In[48]:


# Just run this cell to define fast_distances.

def fast_distances(test_row, train_rows):
    """An array of the distances between test_row and each row in train_rows.

    Takes 2 arguments:
      test_row: A row of a table containing features of one
        test movie (e.g., test_20.row(0)).
      train_rows: A table of features (for example, the whole
        table train_20)."""
    assert train_rows.num_columns < 50, "Make sure you're not using all the features of the movies table."
    counts_matrix = np.asmatrix(train_rows.columns).transpose()
    diff = np.tile(np.array(test_row), [counts_matrix.shape[0], 1]) - counts_matrix
    np.random.seed(0) # For tie breaking purposes
    distances = np.squeeze(np.asarray(np.sqrt(np.square(diff).sum(1))))
    eps = np.random.uniform(size=distances.shape)*1e-10 #Noise for tie break
    distances = distances + eps
    return distances


# #### Question 3.1.3
# Use the `fast_distances` function provided above to compute the distance from the first movie in the test set to all the movies in the training set, **using your set of 20 features**.  Make a new table called `genre_and_distances` with one row for each movie in the training set and two columns:
# * The `"Genre"` of the training movie
# * The `"Distance"` from the first movie in the test set 
# 
# Ensure that `genre_and_distances` is **sorted in increasing order by distance to the first test movie**.

# In[49]:


# The staff solution took 4 lines of code.
genre_and_distances = train_movies.with_column("Distance", fast_distances(test_20.row(0), train_20)).select("Genre", "Distance").sort("Distance")
genre_and_distances


# In[50]:


_ = ok.grade("q3_1_3")
_ = ok.backup()


# #### Question 3.1.4
# Now compute the 5-nearest neighbors classification of the first movie in the test set.  That is, decide on its genre by finding the most common genre among its 5 nearest neighbors, according to the distances you've calculated.  Then check whether your classifier chose the right genre.  (Depending on the features you chose, your classifier might not get this movie right, and that's okay.)

# In[51]:


# Set my_assigned_genre to the most common genre among these.
my_assigned_genre = most_common("Genre", genre_and_distances.take(np.arange(0,5)))

# Set my_assigned_genre_was_correct to True if my_assigned_genre
# matches the actual genre of the first movie in the test set.
my_assigned_genre_was_correct = my_assigned_genre == "action"

print("The assigned genre, {}, was{}correct.".format(my_assigned_genre, " " if my_assigned_genre_was_correct else " not "))


# In[52]:


_ = ok.grade("q3_1_4")
_ = ok.backup()


# ## 3.2. A classifier function
# 
# Now we can write a single function that encapsulates the whole process of classification.

# #### Question 3.2.1
# Write a function called `classify`.  It should take the following four arguments:
# * A row of features for a movie to classify (e.g., `test_20.row(0)`).
# * A table with a column for each feature (e.g., `train_20`).
# * An array of classes that has as many items as the previous table has rows, and in the same order.
# * `k`, the number of neighbors to use in classification.
# 
# It should return the class a `k`-nearest neighbor classifier picks for the given row of features (the string `'Romance'` or the string `'Action'`).

# In[53]:


def classify(test_row, train_rows, train_classes, k):
    """Return the most common class among k nearest neigbors to test_row."""
    distances = fast_distances(test_row, train_rows)
    genre_and_distances = train_movies.with_column("Distance", fast_distances(test_row, train_rows)).select("Genre", "Distance").sort("Distance")

    return most_common("Genre", genre_and_distances.take(np.arange(0,k)))


# In[54]:


_ = ok.grade("q3_2_1")
_ = ok.backup()


# #### Question 3.2.2
# 
# Assign `king_kong_genre` to the genre predicted by your classifier for the movie "king kong" in the test set, using **11 neighbors** and using your 20 features.

# In[55]:


# The staff solution first defined a row object called king_kong_features.
king_kong_features = row_for_title("king kong")
king_kong_genre = classify(test_20.row(0), train_20, king_kong_features, 11)
king_kong_genre


# In[56]:


_ = ok.grade("q3_2_2")
_ = ok.backup()


# Finally, when we evaluate our classifier, it will be useful to have a classification function that is specialized to use a fixed training set and a fixed value of `k`.

# #### Question 3.2.3
# Create a classification function that takes as its argument a row containing your 20 features and classifies that row using the 11-nearest neighbors algorithm with `train_20` as its training set.

# In[57]:


def classify_one_argument(row):
    return classify(row, train_20, row, 11)

# When you're done, this should produce 'Romance' or 'Action'.
classify_one_argument(test_20.row(0))


# In[58]:


_ = ok.grade("q3_2_3")
_ = ok.backup()


# ## 3.3. Evaluating your classifier

# Now that it's easy to use the classifier, let's see how accurate it is on the whole test set.
# 
# **Question 3.3.1.** Use `classify_one_argument` and `apply` to classify every movie in the test set.  Name these guesses `test_guesses`.  **Then**, compute the proportion of correct classifications. 

# In[59]:


test_guesses = test_20.apply(classify_one_argument)


# In[60]:


proportion_correct = np.count_nonzero(test_movies.column('Genre') == test_guesses) / len(test_guesses)
proportion_correct


# In[61]:


_ = ok.grade("q3_3_1")
_ = ok.backup()


# At this point, you've gone through one cycle of classifier design.  Let's summarize the steps:
# 1. From available data, select test and training sets.
# 2. Choose an algorithm you're going to use for classification.
# 3. Identify some features.
# 4. Define a classifier function using your features and the training set.
# 5. Evaluate its performance (the proportion of correct classifications) on the test set.

# ## 4. Explorations
# Now that you know how to evaluate a classifier, it's time to build a better one.

# #### Question 4.1
# Develop a classifier with better test-set accuracy than `classify_one_argument`.  Your new function should have the same arguments as `classify_one_argument` and return a classification.  Name it `another_classifier`. Then, check your accuracy using code from earlier.
# 
# You can use more or different features, or you can try different values of `k`. (Of course, you still have to use `train_movies` as your training set!) 
# 
# **Make sure you don't reassign any previously used variables here**, such as `proportion_correct` from the previous question.

# In[70]:


# To start you off, here's a list of possibly-useful features:
# FIXME: change these example features
staff_features = make_array("happi", "cop", "secur", "human", "alright",
                            "school", "morn", "ya", "mother")

train_staff = train_movies.select(staff_features)
test_staff = test_movies.select(staff_features)

def another_classifier(row):
    return classify(row, train_staff, test_staff.row(0), 9)

new_test = test_staff.apply(another_classifier)
np.count_nonzero(test_movies.column('Genre') == new_test) / len(new_test)


# Briefly describe what you tried to improve your classifier. 

# *I realized that words which were as far from the dashed line in the graphic as possible would be too unique to show up in some movies, so it would render them useless for classification if they didn't occur. I tried using words a little closer to the line, but still close to the bottom right or top left corner. I also reduced the k value.*

# Congratulations: you're done with the required portion of the project! Time to submit.

# In[71]:


_ = ok.submit()

