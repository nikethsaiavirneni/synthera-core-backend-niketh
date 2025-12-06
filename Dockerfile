FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the whole API folder to preserve its structure
COPY ./synthera_core_backend_api ./synthera_core_backend_api

# Also copy 'com' to the root for Lambda imports
COPY ./synthera_core_backend_api/com ./com

COPY ./synthera_core_backend_api/requirements.txt .
RUN pip install -r requirements.txt

ENV PYTHONPATH="${LAMBDA_TASK_ROOT}"

CMD ["com.dimcon.synthera.controller.lambda_entry_point.lambda_handler"]
