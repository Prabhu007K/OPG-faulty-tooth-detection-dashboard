# Model weights

Place your trained YOLO weights here as **`best.pt`**.

## From Kaggle training

After training in `dataset-training.ipynb`, download:

- `faulty_teeth_model_v1.pt` from Kaggle **Output**, or
- `runs/detect/train6/weights/best.pt`

Rename or copy the file to:

```
models/best.pt
```

Restart the app after adding the file.

## Custom path

Set environment variable `MODEL_PATH` to use a different file location.
