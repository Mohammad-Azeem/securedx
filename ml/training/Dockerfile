FROM python:3.11-slim

# Install PyTorch and ONNX
RUN pip install --no-cache-dir \
    torch==2.4.0 \
    onnx==1.16.0 \
    onnxruntime==1.18.0 \
    numpy==1.26.0

WORKDIR /app

CMD ["python", "train_model.py"]