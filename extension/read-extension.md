structure of extension

```bash
gwsmaa_chrome_extension/
│
├── manifest.json
├── background.js
├── popup.html
├── popup.js
├── content.js
├── utils.js
├── styles.css
└── assets/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```



**Icons**
Use 16x16, 48x48, and 128x128 icons in the assets folder.


## **Packaging and Installation**


1. Zip the contents of the **extension** folder.
2. Open Chrome and navigate to chrome://extensions/.
3. Enable "Developer mode".
4. Click "Load unpacked" and select the unzipped folder.
5. Your extension should now be ready to use.


