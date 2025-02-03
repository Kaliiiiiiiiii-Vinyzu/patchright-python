<h1 align="center">
    🎭 Patchright Python
</h1>


<p align="center">
    <a href="https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-green">
    </a>
    <a>
        <img src="https://img.shields.io/badge/Based%20on-Playwright-goldenrod">
    </a>
    <a>
        <img src="https://img.shields.io/badge/Driver-Patched-blue">
    </a>
    <a href="https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python/releases/latest">
        <img alt="Patchright Version" src="https://img.shields.io/github/v/release/microsoft/playwright-python?display_name=release&label=Version">
    </a>
    <a href="https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python/releases">
        <img alt="GitHub Downloads (all assets, all releases)" src="https://img.shields.io/pepy/dt/patchright?color=red">
    </a>
    <a href="https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python">
        <img src="https://img.shields.io/badge/Package-Python-seagreen">
    </a>
</p>

#### Patchright is a patched and undetected version of the Playwright Testing and Automation Framework. </br> It can be used as a drop-in replacement for Playwright.

> [!NOTE]  
> This repository serves the Patchright-Python Package. To use Patchright with NodeJS, check out the [NodeJS Package](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-nodejs).
> Also check out the main [Patchright Driver Repository](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)

---

## Install it from PyPI

```bash
# Install Patchright with Pip from PyPI
pip install patchright
```

```bash
# Install Chromium-Driver for Patchright
patchright install chromium
```

---

## Usage
#### Just change the import and use it like playwright. Patchright is a drop-in-replacement for Playwright!

> [!WARNING]  
> Patchright only patches CHROMIUM based browsers. Firefox and Webkit are not supported.

```py
# patchright here!
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://playwright.dev')
    page.screenshot(path=f'example-{p.chromium.name}.png')
    browser.close()
```

```py
import asyncio
# patchright here!
from patchright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://playwright.dev')
        await page.screenshot(path=f'example-{p.chromium.name}.png')
        await browser.close()

asyncio.run(main())
```

### Best Practices

To be completely undetected, use the following configuration:
```py
playwright.chromium.launch_persistent_context(
    user_data_dir="...",
    channel="chromium",
    headless=False,
    no_viewport=True,
    ...
)
```

---

## Patches

### [Runtime.enable](https://vanilla.aslushnikov.com/?Runtime.enable) Leak
This is the biggest Patch Patchright uses. To avoid detection by this leak, patchright avoids using [Runtime.enable](https://vanilla.aslushnikov.com/?Runtime.enable) by executing Javascript in (isolated) ExecutionContexts.

### [Console.enable](https://vanilla.aslushnikov.com/?Console.enable) Leak
Patchright patches this leak by disabling the Console API all together. This means, console functionality will not work in Patchright. If you really need the console, you might be better off using Javascript loggers, although they also can be easily detected.

### Command Flags Leaks
Patchright tweaks the Playwright Default Args to avoid detection by Command Flag Leaks. This (most importantly) affects:
- `--disable-blink-features=AutomationControlled` (added) to avoid navigator.webdriver detection.
- `--enable-automation` (removed) to avoid navigator.webdriver detection.
- `--disable-popup-blocking` (removed) to avoid popup crashing.
- `--disable-component-update` (removed) to avoid detection as a Stealth Driver.
- `--disable-default-apps` (removed) to enable default apps.
- `--disable-extensions` (removed) to enable extensions

### General Leaks
Patchright patches some general leaks in the Playwright codebase. This mainly includes poor setups and obvious detection points.

---

## Stealth

With the right setup, Patchright currently is considered undetectable.
Patchright passes:
- [Brotector](https://kaliiiiiiiiii.github.io/brotector/) ✅ (with [CDP-Patches](https://github.com/Kaliiiiiiiiii-Vinyzu/CDP-Patches/))
- [Cloudflare](https://cloudflare.com/) ✅
- [Kasada](https://www.kasada.io/) ✅
- [Akamai](https://www.akamai.com/products/bot-manager/) ✅
- [Shape/F5](https://www.f5.com/) ✅
- [Bet365](https://bet365.com/) ✅
- [Datadome](https://datadome.co/products/bot-protection/) ✅
- [Fingerprint.com](https://fingerprint.com/products/bot-detection/) ✅
- [CreepJS](https://abrahamjuliot.github.io/creepjs/) ✅
- [Sannysoft](https://bot.sannysoft.com/) ✅
- [Incolumitas](https://bot.incolumitas.com/) ✅
- [IPHey](https://iphey.com/) ✅
- [Browserscan](https://browserscan.net/) ✅
- [Pixelscan](https://pixelscan.net/) ✅

---

## Documentation and API Reference
See the original [Playwright Documentation](https://playwright.dev/python/docs/intro) and [API Reference](https://playwright.dev/python/docs/api/class-playwright)

---

## Bugs
#### The bugs are documented in the [Patchright Driver Repository](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright#bugs).

---

### TODO
#### The TODO is documented in the [Patchright Driver Repository](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright#todo).


---

## Development

Deployment of new Patchright versions are automatic, but bugs due to Playwright codebase changes may occur. Fixes for these bugs might take a few days to be released. 

---

## Support our work

If you choose to support our work, please contact [@vinyzu](https://discord.com/users/935224495126487150) or [@steve_abcdef](https://discord.com/users/936292409426477066) on Discord.

---

## Copyright and License
© [Vinyzu](https://github.com/Vinyzu/)

Patchright is licensed [Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)

---

## Disclaimer

This repository is provided for **educational purposes only**. \
No warranties are provided regarding accuracy, completeness, or suitability for any purpose. **Use at your own risk**—the authors and maintainers assume **no liability** for **any damages**, **legal issues**, or **warranty breaches** resulting from use, modification, or distribution of this code.\
**Any misuse or legal violations are the sole responsibility of the user**. 

---

## Authors

#### Active Maintainer: [Vinyzu](https://github.com/Vinyzu/) </br> Co-Maintainer: [Kaliiiiiiiiii](https://github.com/kaliiiiiiiiii/)
