import xml.etree.ElementTree as ET
import re

h = open("vkld.h", "w")
h.write("""
/*
 * Copyright (c) 2020 WangBin <wbsecg1 at gmail.com>
 */
""")

cpp = open("vkld.cpp", "w")
cpp_content = """
/*
 * Copyright (c) 2020 WangBin <wbsecg1 at gmail.com>
 */
#include <vulkan/vulkan_core.h>
#if defined(_WIN32)
# include <windows.h>
# define dlopen(filename, flags) LoadLibraryA(filename)
# define dlsym(handle, symbol) GetProcAddress((HMODULE)handle, symbol)
# define dlclose(handle) FreeLibrary((HMODULE)handle)
#else
# include <dlfcn.h>
#endif
// https://stackoverflow.com/questions/1113409/attribute-constructor-equivalent-in-vc
#if defined(_MSC_VER) &&!defined(__clang__)
#pragma section(".CRT$XCU", long, read)
#define INIT_FUNC_ADD(f) \
    __declspec(allocate(".CRT$XCU")) static decltype(&f) init_##f = f;
    //__pragma(data_seg(".CRT$XIU")) static decltype(&f) init_##f = f;
#else//if defined(__GNUC__)
#define INIT_FUNC_ADD(f, ...) \
    __attribute__((constructor)) static void init_##f() { f(__VA_ARGS__); }
#endif

static void init_vk();
INIT_FUNC_ADD(init_vk)

struct vk_t {
#define EXPAND_VK(EXPR) decltype(&EXPR) p##EXPR = nullptr;
#include "vkld.h"
#undef EXPAND_VK
};
static vk_t vk;

void init_vk()
{
    constexpr const char vkdso[] =
#if (_WIN32+0)
        "vulkan-1.dll"
#elif (__APPLE__+0)
        "libvulkan.1.dylib"
#else
        "libvulkan.so"
#endif
        ;
    auto libvulkan = dlopen(vkdso, RTLD_NOW | RTLD_LOCAL);
    if (!libvulkan)
        return;
#define EXPAND_VK(X) do { vk.p##X = (decltype(&X))dlsym(libvulkan, #X); } while (false);
#include "vkld.h"
#undef EXPAND_VK
}
extern "C" {
"""

tree = ET.parse('vk.xml')
root = tree.getroot()
commands = root.find('commands')
cmds = []
for cmd in commands.findall('command'):
    # If the <command> doesn't already have a 'name' attribute, set
    # it from contents of its <proto><name> tag.
    name = cmd.get('name')
    if name is None:
        name = cmd.find('proto/name').text

    if re.match('.*[A-Z]$', name): # name.endswith("KHR") or name.endswith("EXT") or name.endswith("NV"):
        continue
    alias = cmd.get('alias')
    if alias:
        continue

    h.write("""
EXPAND_VK({})""".format(name))

    proto = ET.SubElement(cmd, 'proto')
    ret = cmd.find('proto/type').text #ET.SubElement(proto,'type').text

    argtv = []
    argt = []
    argv = []
    params = []
    for par in cmd.findall('param'):
        argtv.append(re.sub(' +', ' ', ET.tostring(par, encoding="us-ascii", method="text").strip()))
        parname = par.find('name') #ET.SubElement(par, 'name')
        argv.append(parname.text.strip())
        par.remove(parname)
        argt.append(re.sub(' +', ' ', ET.tostring(par, encoding="us-ascii", method="text").strip()))
        p = {
            'type': ET.tostring(par, encoding="us-ascii", method="text"),
            'name': parname.text,
        }
        params.append(p)
    cpp_content += """
VKAPI_ATTR {ret} VKAPI_CALL {name}({argtv}) {{
    return vk.p{name}({argv});
}}
""".format(ret=ret, name=name, argtv=", ".join(argtv), argv=", ".join(argv))
    c = {
        'type': ret,
        'name': name,
        'argv': params
    }

cpp_content += """
} // extern "C"
"""
cpp.write(cpp_content)
h.close()
cpp.close()
