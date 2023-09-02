#shader vertex
#version 460 core

layout(location = 0) in vec2 aPosition;

out vec2 position;

void main() {
    gl_Position = vec4(aPosition.x,aPosition.y,0,1);
    position = aPosition;
}

#shader fragment
#version 460 core

out vec4 fragColor;
in vec2 position;

uniform double centerx;
uniform double centery;
uniform double whx;
uniform double why;

uniform double cr = 0.28;
uniform double ci = 0.008;

const float bailout = 100;
const int maxIters = 200;

float fzm;

vec3 paletteWiki(float i) {
    float r;
    if (i < 0.16) {
        r = i/0.16;
        return vec3(0,0.0275,0.392) * (1-r) + vec3(0.125,0.420,0.796) * r;
    } else if (i < 0.42) {
        r = (i-0.16)/0.26;
        return vec3(0.125,0.420,0.796) * (1-r) + vec3(0.929,1,1) * r;
    } else if (i < 0.6425) {
        r = (i-0.42)/0.2225;
        return vec3(0.929,1,1) * (1-r) + vec3(1,0.667,0) * r;
    } else if (i < 0.8575) {
        r = (i-0.6425)/0.215;
        return vec3(1,0.667,0) * (1-r) + vec3(0,0.0078,0) * r;
    }

    r = (i-0.8575)/0.1425;
    return vec3(0,0.0078,0) * (1-r) + vec3(0,0.0275,0.392) * r;

}


float iterate(double sr, double si) {
    double zr = sr;
    double zi = si;

    double tempr;
    double tempi;

    float iters = 0;

    while (zr*zr + zi*zi < bailout*bailout && iters < maxIters) {
        tempr = (zr*zr-zi*zi) + cr;
        tempi = (2*zr*zi) + ci;
        zr = tempr;
        zi = tempi;
        iters++;
    }

    fzm = float(zr * zr + zi * zi);

    return iters;
}

void main() {
    float n = iterate(centerx + position.x*whx, centery + position.y*why);
    if (n < maxIters) {
        n = n + 1.0 - log((log(fzm) /2)/ log(2)) / log(2);
        fragColor = vec4(paletteWiki(mod(n/10.0,1)),1);
    } else {
        fragColor = vec4(0,0,0,1);
    }

    //fragColor = vec4(paletteWiki((position.x+1)*0.5),1);
}