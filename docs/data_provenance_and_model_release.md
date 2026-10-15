# FloodLens AI — Model and Dataset Provenance

**Status:** preliminary audit, 2026-10-15. This document does **not** certify that every data source permits training or redistribution. Verify the exact original files, the license bundled with each downloaded dataset, and any downstream conditions before releasing the official checkpoint.

## 1. Official model

- Model: YOLO11n-seg **MultiDomain** checkpoint; the BDD100K hard-negative **V3 experiment is not the official model**.
- Local filenames: `models/flood_segmentation/best.pt` and `models/flood_segmentation/best_multidomain.pt`.
- Both files were verified by the project developer to have the exact same SHA-256:

  `82D7BE3E54BA74628F7BE86334CA10E8F4D4B7327AC224FC7787EFDE5E1050B3`

- Ultralytics states that YOLO models and derivatives default to **AGPL-3.0** (or applicable Enterprise terms). FloodLens AI's original application source is public under AGPL-3.0.
- Ultralytics licensing: https://www.ultralytics.com/license
- **Weights are not yet published.** A GitHub Release will be prepared only after the remaining data-origin and licensing questions are documented or resolved.

## 2. Evidence from the repository's MultiDomain dataset-builder

The source code at `src/dataset/build_combined_dataset.py` constructs:

| Dataset | Role | Images | Licensing status |
| --- | --- | ---: | --- |
| RuaLivreIA | training | 1,040 | **CC BY 4.0** shown on the Roboflow Universe dataset page; attribution required |
| Deepflood, UFES-prepared copy | training | 1,002 | **Undetermined for this exact download** |
| Sazara, UFES-prepared copy | training | 241 | **Undetermined for this exact download** |
| Hard-negative images | training | 63 (21 images repeated 3 times) | **Original individual files and licenses require audit** |
| RuaLivreIA | validation | 99 | CC BY 4.0 as indicated above |
| WebCOOS, UFES-prepared copy | validation | 35 | **Undetermined for this exact download** |

Total: **2,346 training image records** and **134 validation records**. The hard-negative 63 count represents 21 unique images repeated three times; it must not be described as 63 independent images.

These figures describe how the checked-in dataset-builder was configured; they should not be misrepresented as a cryptographically proven manifest of the training run. The local raw datasets and the training logs would be needed to establish exact file-level provenance.

## 3. Identified sources

### RuaLivreIA — license identified

- Original dataset page: https://universe.roboflow.com/frank-oliveira/rualivreia
- Project: `frank-oliveira/rualivreia`; license shown on its page as **Creative Commons Attribution 4.0 (CC BY 4.0)**.
- Cite/credit `frank-oliveira`, dataset title, source URL, the CC BY 4.0 license, and indicate adaptation to YOLO training as applicable.
- Verify that the locally downloaded version matches the intended dataset/version (the project previously used version 1).

### Deepflood — source disambiguation is essential

The **street-level Deepflood** described by Chaudhary et al. (2020) contains 8,145 flood images, with 1,259 images carrying pixel-level object annotations. It is discussed in Wang et al.'s urban flood segmentation study, alongside Sazara and WebCOOS:

- https://doi.org/10.1016/j.envsoft.2023.105939
- https://doi.org/10.1016/j.isprsjprs.2020.07.003

This is **not automatically the same resource** as the unrelated 2025 aerial/satellite `DEEPFLOOD DATASET` posted to Figshare under CC BY 4.0:

- https://figshare.com/articles/dataset/DEEPFLOOD_DATASET_High-Resolution_Dataset_for_Accurate_Flood_Mappingand_Segmentation/28328339

**Do not apply the Figshare license to the street-level source.** The exact licensing and distribution rights for the UFES-prepared copy still need the original archive or publisher's terms.

### Sazara — status unresolved

- Research lineage: Cem Sazara et al. (2019), *Detecting floodwater on roadways from image data with handcrafted features and deep transfer learning*. https://arxiv.org/abs/1909.00125
- Dataset license and permission to redistribute the exact UFES-prepared image/mask subset **have not been verified**.

### WebCOOS — status unresolved

- WebCOOS is a coastal/urban camera program discussed in the Wang et al. article above.
- The exact 35 images/segmentation masks used for validation require source terms; license and distribution permission are **not established** by merely having access to the files.

### Hard negatives — status unresolved

The builder adds 21 unique images repeated three times, selected for the MultiDomain base. Their per-file source URLs and licenses must be reconciled against the original `data/negative_training/prepared` and any associated manifests. Do not conflate these with the separately trained BDD100K V3 set.

### BDD100K — experimental V3 only

The 108 hard-negative BDD100K images were used to train the **experimental V3 candidate**, not the selected official MultiDomain checkpoint. Do not imply those 108 samples were part of the model now deployed.

## 4. Conditions before making a public weights release

- [ ] Retrieve and review the original UFES dataset archive/readme/license for the **exact downloaded** Deepflood, Sazara and WebCOOS subsets.
- [ ] Find source URLs and individual licenses for the 21 unique MultiDomain hard-negative images.
- [ ] Resolve any conditions restricting training, derivative use, model distribution, attribution, and competition use.
- [ ] Record complete dataset/source author attributions in the report and README.
- [ ] Validate the official `best.pt` SHA-256 matches this document prior to any upload.
- [ ] Publish only **authorized** binary model weights and their separate model card; **do not** include any original training images, labels or unapproved media in the release.
- [ ] Test Docker and API from a clean clone plus the authorized model file.

**Caution:** A dataset's copyright status and whether trained weights count as a derivative are fact-specific. This document does not determine legal rights over the trained weights. If permissions cannot be confirmed, seek authorization or provide judges with a controlled demonstration while resolving distribution rights.

## 5. Further references

- Ultralytics YOLO licensing: https://www.ultralytics.com/license
- RuaLivreIA Roboflow dataset card: https://universe.roboflow.com/frank-oliveira/rualivreia
- Yidi Wang et al. (2024), urban flood extent segmentation from surveillance cameras: https://doi.org/10.1016/j.envsoft.2023.105939
- Cem Sazara et al. (2019): https://arxiv.org/abs/1909.00125
- Priyanka Chaudhary et al. (2020): https://doi.org/10.1016/j.isprsjprs.2020.07.003
