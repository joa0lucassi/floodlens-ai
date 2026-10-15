# FloodLens AI — Model and Dataset Provenance

**Status:** provenance audit updated 2026-10-15. The HydroShare source and its CC BY 4.0 resource-level license have been identified. This does **not** certify that every upstream image contributor granted all permissions or that model weights can automatically be redistributed.

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
| Deepflood, HydroShare package | training | 1,002 | **HydroShare resource states CC BY 4.0**; upstream third-party rights to review |
| Sazara, HydroShare package | training | 241 | **HydroShare resource states CC BY 4.0**; upstream third-party rights to review |
| Hard-negative images | training | 63 (21 images repeated 3 times) | **Original individual files and licenses require audit** |
| RuaLivreIA | validation | 99 | CC BY 4.0 as indicated above |
| WebCOOS, HydroShare package | validation | 35 | **HydroShare resource states CC BY 4.0**; upstream third-party rights to review |

Total: **2,346 training image records** and **134 validation records**. The hard-negative 63 count represents 21 unique images repeated three times; it must not be described as 63 independent images.

These figures describe how the checked-in dataset-builder was configured; they should not be misrepresented as a cryptographically proven manifest of the training run. The local raw datasets and the training logs would be needed to establish exact file-level provenance.

## 3. Identified sources

### RuaLivreIA — license identified

- Original dataset page: https://universe.roboflow.com/frank-oliveira/rualivreia
- Project: `frank-oliveira/rualivreia`; license shown on its page as **Creative Commons Attribution 4.0 (CC BY 4.0)**.
- Cite/credit `frank-oliveira`, dataset title, source URL, the CC BY 4.0 license, and indicate adaptation to YOLO training as applicable.
- Verify that the locally downloaded version matches the intended dataset/version (the project previously used version 1).

### Deepflood, Sazara and WebCOOS — HydroShare resource identified

**Original package:** [Urban Flood Image Dataset](https://www.hydroshare.org/resource/24866122a6ee456c8f7c80aa87a9abcb/), publicly attributed as:

> Wang, Y. (2024). *Urban Flood Image Dataset*. HydroShare. https://www.hydroshare.org/resource/24866122a6ee456c8f7c80aa87a9abcb/

The resource landing page explicitly states: **Creative Commons Attribution (CC BY 4.0)**, linking to https://creativecommons.org/licenses/by/4.0/. This license is displayed in the resource metadata and the download acceptance dialog rather than as `LICENSE` files in each ZIP.

**Provenance from the project's actual download workflow:** `Deepflood.zip`, `Sazara.zip`, and `WebCOOS.zip` were downloaded as the three archives from this exact HydroShare resource and retained together locally under `FloodLens_UFES`. The developer verified these three ZIPs contain 2,082, 508, and 73 archive entries, respectively, and **none has a named README/LICENSE/CITATION file**. Note that ZIP entry counts are not counts of independent training images.

**Attribution recommendation:** credit both the HydroShare resource publisher (Y. Wang, 2024, URL, CC BY 4.0) and the underlying dataset authors whenever known:

- **Deepflood (street-level):** Chaudhary et al., *Flood level estimation from social media images*, 2020; verify exact title and bibliographic details before the final paper citation. https://doi.org/10.1016/j.isprsjprs.2020.07.003
- **Sazara:** Cem Sazara, Mecit Cetin and Khan M. Iftekharuddin (2019), *Detecting floodwater on roadways from image data with handcrafted features and deep transfer learning*. https://arxiv.org/abs/1909.00125
- **WebCOOS:** camera imagery used within the urban flood study; original camera/data-owner permissions and attribution need checking.
- **Study presenting these sources together:** Yidi Wang et al. (2024), *Urban flood extent segmentation and evaluation from real-world surveillance camera images using deep convolutional neural network*. https://doi.org/10.1016/j.envsoft.2023.105939

**Important licensing caveat:** The *HydroShare resource's* CC BY 4.0 declaration is now verified. It does not, by itself, prove that every third-party photograph included in the resource was lawfully relicensed or that all downstream derivative-model distribution questions are settled. We should not claim per-image original licenses have been audited. Preserve the explicit resource attribution and seek any necessary clarification before broader reuse/distribution.

**Do not confuse Deepflood resources.** An unrelated `DEEPFLOOD DATASET` (2025) on Figshare concerns aerial/remote-sensing imagery: https://figshare.com/articles/dataset/DEEPFLOOD_DATASET_High-Resolution_Dataset_for_Accurate_Flood_Mappingand_Segmentation/28328339 . Its license is not the basis for our street-level ZIP.

### Hard negatives — 21 originals, provenance not documented

On 2026-10-05, the project developer manually supplied **21 negative images** (seven in each of three categories) to `data/negative_training/images`. The images were normalized to filenames `floodlens_negative_001.jpg` through `floodlens_negative_021.jpg`, paired with empty YOLO segmentation labels, copied into `data/negative_training/prepared/` and packaged as `data/negative_training/negative_training.zip`.

The project developer's 2026-10-15 local inspection confirmed 21 images in `images/`, 21 in `prepared/images/`, 21 annotation files in `prepared/labels/`, and the archive `negative_training.zip`. No CSV, JSON, Markdown, README, license, or attribution manifest was found in the local dataset tree. The original conversations did not record exact source URLs, authors, or individual image licenses.

The MultiDomain builder repeats **each of these 21 images three times** to form 63 training records. Repeats are **not** independent or distinct images. The archive creation date and the renamed filenames do **not** establish the original photographs' authorship, usage permissions, or license.

**Audit status: provenance unresolved.** Do not represent these images as CC BY, CC0, Pexels, Unsplash, or as personally photographed without evidence. Do not publish their ZIP or their derived dataset. Before deciding whether to publish model weights, determine the images' original origin and permissions and consider the legal implications for model distribution. Keep this set distinct from the later BDD100K V3 experiment.

### BDD100K — experimental V3 only

The 108 hard-negative BDD100K images were used to train the **experimental V3 candidate**, not the selected official MultiDomain checkpoint. Do not imply those 108 samples were part of the model now deployed.

## 4. Conditions before making a public weights release

- [x] Identify original HydroShare resource for the three ZIP files and confirm its **CC BY 4.0 resource-level** statement.
- [ ] Add complete HydroShare/Wang and original dataset-author credits to project-facing documentation; investigate third-party rights where relevant.
- [x] Reconcile the 21-file local negative-training archive with the documented original workflow; confirmed that no per-image source manifest was created.
- [ ] Establish the original authorship, source URLs and permitted uses of those 21 images before marking their rights cleared.
- [ ] Resolve any conditions restricting training, derivative use, model distribution, attribution, and competition use.
- [ ] Record complete dataset/source author attributions in the report and README.
- [ ] Validate the official `best.pt` SHA-256 matches this document prior to any upload.
- [ ] Publish only **authorized** binary model weights and their separate model card; **do not** include any original training images, labels or unapproved media in the release.
- [ ] Test Docker and API from a clean clone plus the authorized model file.

**Caution:** A dataset's copyright status and whether trained weights count as a derivative are fact-specific. This document does not determine legal rights over the trained weights. If permissions cannot be confirmed, seek authorization or provide judges with a controlled demonstration while resolving distribution rights.

## 5. Further references

- Ultralytics YOLO licensing: https://www.ultralytics.com/license
- RuaLivreIA Roboflow dataset card: https://universe.roboflow.com/frank-oliveira/rualivreia
- HydroShare Urban Flood Image Dataset (Wang, Y., 2024), CC BY 4.0: https://www.hydroshare.org/resource/24866122a6ee456c8f7c80aa87a9abcb/
- Yidi Wang et al. (2024), urban flood extent segmentation from surveillance cameras: https://doi.org/10.1016/j.envsoft.2023.105939
- Cem Sazara et al. (2019): https://arxiv.org/abs/1909.00125
- Priyanka Chaudhary et al. (2020): https://doi.org/10.1016/j.isprsjprs.2020.07.003
