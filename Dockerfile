
# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory in the container
WORKDIR /var/task

# Copy the backend directory entirely
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# RUN pip install apig-wsgi

# Install project dependencies
# RUN pip install awslambdaric

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=CONFIG.settings
ENV PYTHONUNBUFFERED=1

# Create static files directory
RUN mkdir -p staticfiles

# Collect static files for Django
RUN python manage.py collectstatic --noinput

# Copy static files to a location Lambda can serve
# RUN cp -r staticfiles/* ${LAMBDA_TASK_ROOT}/

# The CMD will be used by AWS Lambda
CMD ["lambda_handler.handler"]
