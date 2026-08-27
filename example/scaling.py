import sys
import os
import argparse
import ctypes
import subprocess
import numpy as np
from PIL import Image
from OpenGL import EGL
from OpenGL.EGL import *
from OpenGL.GL import *


def build_shaders(shader_dir):
    frag_path = os.path.join(shader_dir, 'out', 'plushie.frag')
    vert_path = os.path.join(shader_dir, 'out', 'plushie.vert')
    if os.path.isfile(frag_path) and os.path.isfile(vert_path):
        with open(frag_path, 'r') as f:
            frag_source = f.read()
        with open(vert_path, 'r') as f:
            vert_source = f.read()
        return vert_source, frag_source
    try:
        result = subprocess.run(
            ['ninja', '-C', shader_dir],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        raise RuntimeError('ninja not found in PATH')
    if result.returncode != 0:
        raise RuntimeError('ninja build failed:\n' + result.stderr)
    with open(frag_path, 'r') as f:
        frag_source = f.read()
    with open(vert_path, 'r') as f:
        vert_source = f.read()
    return vert_source, frag_source


def compile_shader(shader_type, source):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        log = glGetShaderInfoLog(shader).decode()
        glDeleteShader(shader)
        raise RuntimeError('Shader compile error:\n' + log)
    return shader


def create_program(vert_source, frag_source):
    vert = compile_shader(GL_VERTEX_SHADER, vert_source)
    frag = compile_shader(GL_FRAGMENT_SHADER, frag_source)
    program = glCreateProgram()
    glAttachShader(program, vert)
    glAttachShader(program, frag)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        log = glGetProgramInfoLog(program).decode()
        raise RuntimeError('Program link error:\n' + log)
    glDeleteShader(vert)
    glDeleteShader(frag)
    return program


def init_egl():
    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    if display == EGL_NO_DISPLAY:
        raise RuntimeError('Failed to get EGL display')
    major = EGLint()
    minor = EGLint()
    if not eglInitialize(display, ctypes.byref(major), ctypes.byref(minor)):
        raise RuntimeError('Failed to initialize EGL')
    eglBindAPI(EGL_OPENGL_ES_API)
    config_attribs = (EGLint * 15)(
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    )
    config = EGLConfig()
    num_configs = EGLint()
    if not eglChooseConfig(display, config_attribs, ctypes.byref(config), 1, ctypes.byref(num_configs)):
        raise RuntimeError('Failed to choose EGL config')
    context_attribs = (EGLint * 5)(
        EGL_CONTEXT_MAJOR_VERSION, 3,
        EGL_CONTEXT_MINOR_VERSION, 0,
        EGL_NONE
    )
    context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attribs)
    if context == EGL_NO_CONTEXT:
        raise RuntimeError('Failed to create EGL context')
    pbuffer_attribs = (EGLint * 5)(
        EGL_WIDTH, 1,
        EGL_HEIGHT, 1,
        EGL_NONE
    )
    surface = eglCreatePbufferSurface(display, config, pbuffer_attribs)
    if surface == EGL_NO_SURFACE:
        raise RuntimeError('Failed to create EGL pbuffer surface')
    if not eglMakeCurrent(display, surface, surface, context):
        raise RuntimeError('Failed to make EGL context current')
    return display, surface, context


def main():
    parser = argparse.ArgumentParser(description='Plushie GLES image upscaler')
    parser.add_argument('input', help='Input image path')
    parser.add_argument('-o', '--output', required=True, help='Output image path')
    parser.add_argument('-s', '--scale', type=float, default=2.0, help='Scale factor')
    parser.add_argument('-W', '--width', type=int, help='Output width')
    parser.add_argument('-H', '--height', type=int, help='Output height')
    parser.add_argument('--shader-dir', required=True, help='Directory containing plushie shader files')
    parser.add_argument('--thresh-grad-low', type=float, default=0.0)
    parser.add_argument('--thresh-grad-high', type=float, default=0.0)
    parser.add_argument('--thresh-var-low', type=float, default=0.0)
    parser.add_argument('--thresh-var-high', type=float, default=0.0)
    args = parser.parse_args()

    img = Image.open(args.input).convert('RGBA')
    in_w, in_h = img.size
    if args.width and args.height:
        out_w, out_h = args.width, args.height
    elif args.width:
        out_w = args.width
        out_h = int(in_h * out_w / in_w)
    elif args.height:
        out_h = args.height
        out_w = int(in_w * out_h / in_h)
    else:
        out_w = int(in_w * args.scale)
        out_h = int(in_h * args.scale)

    display, surface, context = init_egl()

    vert_source, frag_source = build_shaders(args.shader_dir)
    program = create_program(vert_source, frag_source)

    vertices = np.array([
        -1.0, -1.0, 0.0, 1.0,
         1.0, -1.0, 1.0, 1.0,
        -1.0,  1.0, 0.0, 0.0,
         1.0,  1.0, 1.0, 0.0,
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))

    img_data = np.array(img, dtype=np.uint8)
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, in_w, in_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    out_tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, out_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, out_w, out_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, out_tex, 0)
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        raise RuntimeError('Framebuffer incomplete')

    glViewport(0, 0, out_w, out_h)
    glUseProgram(program)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, tex)
    glUniform1i(glGetUniformLocation(program, 'uTex'), 0)
    glUniform2f(glGetUniformLocation(program, 'uTexSize'), float(in_w), float(in_h))
    glUniform2f(glGetUniformLocation(program, 'uOutSize'), float(out_w), float(out_h))
    glUniform1f(glGetUniformLocation(program, 'uThreshGradLow'), args.thresh_grad_low)
    glUniform1f(glGetUniformLocation(program, 'uThreshGradHigh'), args.thresh_grad_high)
    glUniform1f(glGetUniformLocation(program, 'uThreshVarLow'), args.thresh_var_low)
    glUniform1f(glGetUniformLocation(program, 'uThreshVarHigh'), args.thresh_var_high)

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    result = np.zeros((out_h, out_w, 4), dtype=np.uint8)
    glReadPixels(0, 0, out_w, out_h, GL_RGBA, GL_UNSIGNED_BYTE, result)
    result = np.flipud(result)
    out_img = Image.fromarray(result, 'RGBA')
    if args.output.lower().endswith(('.jpg', '.jpeg')):
        out_img = out_img.convert('RGB')
    out_img.save(args.output)

    glDeleteFramebuffers(1, [fbo])
    glDeleteTextures(2, [tex, out_tex])
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])
    glDeleteProgram(program)
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)
    eglDestroySurface(display, surface)
    eglDestroyContext(display, context)
    eglTerminate(display)

    print('Saved ' + str(out_w) + 'x' + str(out_h) + ' -> ' + args.output)


if __name__ == '__main__':
    main()