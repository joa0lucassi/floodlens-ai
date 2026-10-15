# Optional Segmentation Visualization — Experimental Branch

This change is isolated on `feat/segmentation-preview` pending local testing.

## Scope

The user uploads an image or recorded video. The normal segmentation, temporal rule and risk engine are **unchanged**. When requested, the API additionally returns one visually annotated still image to help users understand *where the model predicted water*.

For video uploads, this is **not an annotated video stream**: it is a single, representative sampled frame chosen as the frame with the highest visually segmented image area. The frame is re-inferred once for its preview; this second prediction does not affect any video classifications or temporal/risk statistics. The annotation is for explanation only and does not verify a flood or estimate water depth.

## API Contract

Both routes continue to support the original request and JSON response:

- `POST /analyze/image`
- `POST /analyze/video`

Optional query parameter: `?include_visualization=true`

When true, the response includes:

~~~json
{
  "visualization": {
    "image_data_url": "data:image/jpeg;base64,...",
    "has_segmented_pixels": true,
    "time_seconds": 4.0,
    "selection_method": "largest_segmented_area"
  }
}
~~~

The `time_seconds` and `selection_method` fields are added for video only. The image data URL is optional and appears only when requested. Keep `include_visualization` off for automated API clients that do not need an image.

The output shows cyan tint within predicted polygons, with white outlines. The preview is downscaled to at most 960 pixels wide. The overlay is returned only to the calling browser and is **excluded from analysis JSON written to S3**. The normal S3 upload behavior is not changed.

The current dashboard requests previews automatically, displays them next to the original media, and keeps them out of the in-browser analysis history records. A redesigned Kimi dashboard should retain this behavior and avoid simulated sample results.

## Validation Checklist (not yet completed)

1. Pull or switch to `feat/segmentation-preview` and rebuild the local Docker image.
2. Upload `data/flood_sample.mp4` from the dashboard.
3. Check temporal result is CONFIRMED with 7 samples / 3 windows and risk MODERATE, matching the baseline.
4. Check the cyan segmentation overlay displays a real representative image from the uploaded video, not a hard-coded example.
5. Test one valid JPG or PNG and one negative video.
6. Check that the API works unchanged without `include_visualization`, that S3 is not required for local use, and that page reload clears local history.

Only after successful user-side smoke tests should this branch be merged to `main` and described as validated.
