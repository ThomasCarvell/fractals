from OpenGL.GL import *
import pygame
import numpy as np
import ctypes

class program():

    REFERENCE = [GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER]
    
    FRAGMENT = 0
    VERTEX = 1
    GEOMETRY = 2
    TESSCONTROL = 3
    TESSEVAL = 4

    def _compileShader(self, type, source):
        shader = glCreateShader(type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        compiled = glGetShaderiv(shader, GL_COMPILE_STATUS)
        
        if not compiled:
            info = glGetShaderInfoLog(shader).decode()
            glDeleteShader(shader)

            raise Exception("Shader compile error: " + info)

        return shader

    def __init__(self, filename):
        shaderSources = ['' for i in range(5)]

        mode = -1

        with open(filename,"r") as f:
            while line := f.readline():
                if line.find("#shader") != -1:
                    if line.find("fragment") != -1: mode = self.FRAGMENT
                    elif line.find("vert") != -1: mode = self.VERTEX
                    elif line.find("geo") != -1: mode = self.GEOMETRY
                    elif line.find("tesseval") != -1: mode = self.TESSEVAL
                    elif line.find("tesscontrol") != -1: mode = self.TESSCONTROL
                    continue

                if mode == -1:
                    continue

                shaderSources[mode] += line

        self.program = glCreateProgram()
        self.uniforms = {}

        shaders = [0, 0, 0, 0, 0]

        for type,shader in enumerate(shaderSources):
            if not shader:
                continue

            shaders[type] = self._compileShader(self.REFERENCE[type],shaderSources[type])

        for shader in shaders:
            if not shader:
                continue

            glAttachShader(self.program,shader)

        glLinkProgram(self.program)
        glValidateProgram(self.program)

        for i in range(glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS)):
            uniform = glGetActiveUniform(self.program, i);
            self.uniforms[uniform[0].decode()] = glGetUniformLocation(self.program, uniform[0].decode())

    def use(self):
        glUseProgram(self.program)

    def setMatrix4(self, name, value):
        glProgramUniformMatrix4fv(self.program, self.uniforms[name], 1, False, value)

    def setVector4(self, name, value):
        glProgramUniform3fv(self.program, self.uniforms[name], 1, False, value)

    def setDouble(self, name, value):
        glProgramUniform1d(self.program, self.uniforms[name], value)

class camera:

    def __init__(self,center,wh):
        self.topleft = np.array([center[0]-wh[0], center[1]-wh[1]], dtype = np.float32)
        self.bottomright = np.array([center[0]+wh[0], center[1]+wh[1]], dtype = np.float32)

    def zoom(self,mult):
        center = [(self.bottomright[0]+self.topleft[0])/2.0, (self.bottomright[1]+self.topleft[1])/2.0]
        wh = [(self.bottomright[0]-self.topleft[0])/2 * mult, (self.bottomright[1]-self.topleft[1])/2 * mult]

        self.topleft = [center[0]-wh[0], center[1]-wh[1]]
        self.bottomright = [center[0]+wh[0], center[1]+wh[1]]

    def pan(self, dx, dy):
        wh = [(self.bottomright[0]-self.topleft[0])/2, (self.bottomright[1]-self.topleft[1])/2]

        self.topleft[0] += dx*wh[0]
        self.bottomright[0] += dx*wh[0]
        self.topleft[1] += dy*wh[1]
        self.bottomright[1] += dy*wh[1]

    def getMetrics(self):
        return ([(self.bottomright[0]+self.topleft[0])/2, (self.bottomright[1]+self.topleft[1])/2],[(self.bottomright[0]-self.topleft[0])/2, (self.bottomright[1]-self.topleft[1])/2])

class screenspace():

    def __init__(self):
        self.verticies = np.array([[-1,-1],[1,-1],[-1,1],[1,1]], dtype = np.float32)
        self.faces = np.array([0,1,2,1,2,3], dtype = np.uint)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)

        glBufferData(GL_ARRAY_BUFFER, self.verticies.itemsize * self.verticies.size, self.verticies, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, False, 2*4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.faces.itemsize * self.faces.size, self.faces, GL_STATIC_DRAW)

        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(0))

class app():

    FPS = 60
    WIDTH = 1920
    HEIGHT = 1200

    def __init__(self):
        pygame.init()
        self.root = pygame.display.set_mode((self.WIDTH,self.HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN, vsync=1)
        self.clock = pygame.time.Clock()

    def run(self):
        self.mainloop()

    def mainloop(self):

        juliaShaders = program("juliaSets.glsl")
        mandelShaders = program("mandelBrot.glsl")

        mandelCamera = camera([0,0],[2,2 * (self.HEIGHT/self.WIDTH)])
        juliaCamera = camera([0,0],[2,2 * (self.HEIGHT/self.WIDTH)])

        juliacr = 0
        juliaci = 0

        mandel = True
        activeCamera = mandelCamera

        scrnSpace = screenspace()

        dtime = 0

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and mandel:
                        running = False

            keys = pygame.key.get_pressed()

            if keys[pygame.K_d]:
                activeCamera.pan(0.025 * dtime,0)
            if keys[pygame.K_a]:
                activeCamera.pan(-0.025 * dtime,0)
            if keys[pygame.K_w]:
                activeCamera.pan(0,0.025 * dtime)
            if keys[pygame.K_s]:
                activeCamera.pan(0,-0.025 * dtime)
            if keys[pygame.K_e]:
                activeCamera.zoom(0.95)
            if keys[pygame.K_q]:
                activeCamera.zoom(1.05263158)

            if keys[pygame.K_RIGHT]:
                juliacr += 0.001
            if keys[pygame.K_LEFT]:
                juliacr -= 0.001
            if keys[pygame.K_UP]:
                juliaci += 0.001
            if keys[pygame.K_DOWN]:
                juliaci -= 0.001

            mandelMetrics = mandelCamera.getMetrics()

            if pygame.mouse.get_pressed(3)[0] and mandel:
                mpos = pygame.mouse.get_pos()
                juliacr =  (mpos[0]*2 / self.WIDTH - 1) * mandelMetrics[1][0] + mandelMetrics[0][0]
                juliaci =  (mpos[1]*2 / self.HEIGHT - 1) * mandelMetrics[1][1] + mandelMetrics[0][1]
                juliaCamera = camera([0,0],[2,2 * (self.HEIGHT/self.WIDTH)])
                activeCamera = juliaCamera
                mandel = False

            if keys[pygame.K_ESCAPE] and not mandel:
                activeCamera = mandelCamera
                mandel = True

            juliaMetrics = juliaCamera.getMetrics()

            juliaShaders.setDouble("centerx", juliaMetrics[0][0])
            juliaShaders.setDouble("centery", juliaMetrics[0][1])
            juliaShaders.setDouble("whx", juliaMetrics[1][0])
            juliaShaders.setDouble("why", juliaMetrics[1][1])
            juliaShaders.setDouble("cr", juliacr)
            juliaShaders.setDouble("ci", juliaci)

            mandelShaders.setDouble("centerx", mandelMetrics[0][0])
            mandelShaders.setDouble("centery", mandelMetrics[0][1])
            mandelShaders.setDouble("whx", mandelMetrics[1][0])
            mandelShaders.setDouble("why", mandelMetrics[1][1])

            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if mandel:
                mandelShaders.use()
            else:
                juliaShaders.use()

            scrnSpace.draw()

            pygame.display.flip()
            dtime = self.clock.tick(self.FPS)/ 50


    def __del__(self):
        pygame.quit()

if __name__ == "__main__":
    try:
        application = app()
        application.run()
    except Exception as e:
        raise e