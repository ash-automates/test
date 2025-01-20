#!/bin/bash

# Create the main project directory
mkdir -p project
cd project || exit

# Create main Flask application files
touch app.py config.py requirements.txt

# Create the static folder and its subfolders
mkdir -p static/css static/js static/images

touch static/css/styles.css static/js/scripts.js

# Create the templates folder and its subfolders
mkdir -p templates/{articles,stock,suppliers,errors}

touch templates/base.html \
      templates/dashboard.html \
      templates/articles/{list.html,new.html,edit.html} \
      templates/stock/{list.html,new_entry.html,new_exit.html} \
      templates/suppliers/{list.html,new.html,details.html} \
      templates/errors/{404.html,500.html}

# Create migrations folder
mkdir -p migrations

# Create instance folder and config file
mkdir -p instance

touch instance/config.py

# Print completion message
echo "Project structure created successfully!"

