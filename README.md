# vkld
vulkan api loader without user code change. Only 1.0 core apis are included

## How to Use
- (optional) download https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/master/xml/vk.xml
- (optional) run vkld.py
- add generated vkld.h, vkld.cpp in your c/c++ project (add linker flag -nostdlib++ for c programs)
- remove vulkan in your linker flags
