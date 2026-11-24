"""Witchaven II port, second stage (after port_wh2.py): the remaining DOS-isms
found by the compiler. usage: port_wh2b.py <jfwhaven2 tree>"""
import os, re, sys

SRC = os.path.join(sys.argv[1], 'src')
BS = chr(92)

def load(name):
    return open(os.path.join(SRC, name), encoding='latin1', newline='').read().replace('\r\n', '\n')

def save(name, s):
    open(os.path.join(SRC, name), 'w', encoding='latin1', newline='\n').write(s)

def delete_block(s, head):
    while True:
        m = re.search(r'(?m)^[ \t]*' + re.escape(head) + r'[^\n]*\{[ \t]*\n', s)
        if not m:
            return s
        depth = 0
        j = s.index('{', m.start())
        while j < len(s):
            if s[j] == '{':
                depth += 1
            elif s[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = j + 1
        while end < len(s) and s[end] == '\n':
            end += 1
        s = s[:m.start()] + s[end:]

def delete_calls(s, name):
    """Remove statements that are a bare call of `name`."""
    return re.sub(r'(?m)^[ \t]*' + re.escape(name) + r'\(\);[ \t]*\n', '', s)

# whaven.c
s = load('whaven.c')
s = s.replace('\nspikesector[64];', '\nshort spikesector[64];')
s = s.replace('jmp_buf jmpenv;\n', '')
s = delete_calls(s, 'whvrmon')  # the VR headset monitor
s = re.sub(r'allocache\(&waloff\[(\w+)\], 320L? \* 320L?, &walock\[\1\]\)', r'allocache((void **)&waloff[\1], 320 * 320, &walock[\1])', s)
s = re.sub(r'allocache\(&waloff\[(\w+)\],', r'allocache((void **)&waloff[\1],', s)
# the sequel plays its videos by number
s = s.replace('int app_main(int argc, const char * const argv[]) {', '''// the sequel's videos, by the DOS game's numbering
static const char *smknames[] = { "intro", "ending1", "stairs", "ending2", "ending3" };
int smkplayseqnum(int s) {
    if (s < 0 || s >= 5) return 0;
    return smkplayseq((char *)smknames[s]);
}
unsigned short wDIGIVol = 0x7fff, wMIDIVol = 0x7f; // the DOS sound setup's volumes (unused here)
char tempbuf[576]; // the DOS text-mode module's (whmsc.c) scratch buffer
char chainstat;    // old Build engine globals the game still names
int transarea;

int app_main(int argc, const char * const argv[]) {''', 1)
s = s.replace('netcheckargs(argc, (char **)argv);', 'netcheckargs(argc, argv);')
s = s.replace('char configFile[_MAX_PATH];', 'char configFile[BMAX_PATH];')
# setOptions: the sound device checks went with the DOS sound setup; their else branches too
s = s.replace('     else {\n          option[8] = option[9] = 0;\n     }\n', '')
s = s.replace('     else {\n          option[10] = option[11] = 0;\n     }\n', '')
save('whaven.c', s)

# whinp.c
s = load('whinp.c')
s = s.replace('     short bstatus,\n          mousx,\n          mousy;', '     int bstatus,\n          mousx,\n          mousy;')
s = delete_block(s, 'if (vfx1enabled || iglassenabled || cyberenabled)')
s = delete_calls(s, 'jstick')  # the DOS joystick library's poll: the engine fills joyaxis/joyb itself
s = s.replace('char joyb,\n     oldjoyb,', 'char oldjoyb,')
s = re.sub(r'(?m)^(\s*)short\s+mousx,\s*\n', r'\1int mousx,\n', s)
s = s.replace('SND_playSound(S_JUDYDIE)', 'SND_Sound(S_JUDYDIE)')
# WH2TRACE (temporary): what the input routine sees, twice a second
s = s.replace('''     synctics = tics = i;
     lockclock += (int) synctics;
''', '''     synctics = tics = i;
     lockclock += (int) synctics;
     {
          static int tracenext;
          if (getenv("WH2TRACE") && totalclock >= tracenext) {
               tracenext = totalclock + 60;
               buildprintf("trace: totalclock %d synctics %d left %d right %d fwd %d ang %d x %d y %d esc %d dead %d\\n",                    (int)totalclock, synctics, keystatus[keys[KEYLEFT]], keystatus[keys[KEYRIGHT]], keystatus[keys[KEYFWD]],
                    plr->ang, plr->x, plr->y, escapetomenu, playerdie);
          }
     }
''')
s = re.sub(r'(?m)^[ \t]*musiclevel = \(wMIDIVol >> 3\);\n[ \t]*digilevel = \(wDIGIVol >> 11\);\n', '', s)
save('whinp.c', s)

# whmenu.c
s = load('whmenu.c')
s = s.replace('extern char palette[];\n', '')
s = re.sub(r'(?m)^[ \t]*musiclevel = \(wMIDIVol >> 3\);\n[ \t]*digilevel = \(wDIGIVol >> 11\);\n', '', s)
save('whmenu.c', s)

# whfx.c, whobj.c, whplr.c, whtag.c
s = load('whfx.c')
s = s.replace('extern bobbingsectorcnt,\n     bobbingsectorlist[];', 'extern int bobbingsectorcnt,\n     bobbingsectorlist[];')
s = re.sub(r'\bsmkplayseq\((\d)\)', r'smkplayseqnum(\1)', s)
save('whfx.c', s)
s = load('whobj.c')
s = s.replace('extern justwarpedfx;', 'extern int justwarpedfx;')
save('whobj.c', s)
s = load('whplr.c')
s = re.sub(r'\bsmkplayseq\((\d)\)', r'smkplayseqnum(\1)', s)
save('whplr.c', s)
s = load('whtag.c')
s = s.replace('if (clipinsidebox(dax, day, dax2, day2, 512L) == 1) {', 'if (clipinsideboxline(dax, day, dax, day, dax2, day2, 512) == 1) {')
save('whtag.c', s)

# readcfg.c, profile.c: the DOS include and C library names
for name in ('readcfg.c', 'profile.c'):
    s = load(name)
    s = s.replace('#include <sys' + BS + 'types.h>', '#include <sys/types.h>')
    s = s.replace('#include <sys' + BS + 'stat.h>', '#include <sys/stat.h>')
    s = re.sub(r'\bstrcmpi\(', 'strcasecmp(', s)
    s = re.sub(r'itoa\(\s*([^,]+?),\s*([^,]+?),\s*10\s*\)', r'sprintf(\2, "%d", \1)', s)
    s = re.sub(r'itoa\(\s*([^,]+?),\s*([^,]+?),\s*16\s*\)', r'sprintf(\2, "%x", \1)', s)
    s = re.sub(r'\bstricmp\(', 'strcasecmp(', s)
    save(name, s)

# icorp.h: the config arrays are char, keys too, the net and helper prototypes
s = load('icorp.h')
s = s.replace('extern short configKeyboard[], configMouse[], configJoystick[], configGamepad[], configWingman[], configAvenger[];',
              'extern char configKeyboard[], configMouse[], configJoystick[], configGamepad[], configWingman[], configAvenger[];')
s = s.replace('extern int keys[];', '''extern char keys[];
extern unsigned short wDIGIVol, wMIDIVol;
#define TICSPERFRAME 3
#ifndef _MAX_PATH
#define _MAX_PATH BMAX_PATH
#define _MAX_FNAME 256
#define _MAX_EXT 256
#endif''')
s = s.replace('void setOptions(void);', '''void setOptions(void);
int smkplayseqnum(int s);
void dolevelmusic(int level);
void setdelayfunc(void (*func)(), int item, int delay);
// whnet.c (JonoF's)
void netcheckargs(int argc, const char * const argv[]);
void netmarkflag(short i);
void netsendmove(void);
void netshootgun(short s, char guntype);
void netdamageactor(short s, short o);
void dropflagstart(short teamno);
void netdropflag(void);
void netgetmove(void);
void netpickmonster(void);
void initmulti(int numplayers);
void netshutdown(void);
void whnetmon(void);
void netrestartplayer(struct player *plr);''')
save('icorp.h', s)

# whinp.c: the pad. The DOS game read the joystick port (active-low buttons,
# a three-step calibration); here the engine's joyaxis[]/joyb, as JonoF's
# Witchaven on the MiSTer: left stick moves and strafes, right stick turns,
# the eight buttons (joyb bits 2..9: R B A L Y X Select Start) are
# fire, jump, use, run, cast spell, use potion, map, nothing.
s = load('whinp.c')
s = s.replace('''char oldjoyb,
     oldbstatus,
     butbit[] = {0x10, 0x20, 0x40, 0x80},
     mbutbit[] = {0x01, 0x04, 0x02};    // Les 01/17/96
''', '''#define NUMJOYKEYS 8
int oldjoyb,
     butbit[] = {0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x100, 0x200}; // MiSTer: joyb bits 2..9
char oldbstatus,
     mbutbit[] = {0x01, 0x04, 0x02};    // Les 01/17/96
''')
s = s.replace('''int  joyx, joyy,
     joykeys[4],
     jstickenabled = 0,''', '''int  joyx, joyy,
     joykeys[NUMJOYKEYS],
     jstickenabled = 0,''')
s = re.sub(r'''void\ninitjstick\(void\)\n\{\n.*?\n\}\n''', '''void
initjstick(void)
{
     // MiSTer: the core's eight buttons, R B A L Y X Select Start
     static const int misterjoykeys[NUMJOYKEYS] = {KEYFIRE, KEYJUMP, KEYUSE, KEYRUN, KEYCAST, KEYUSEP, KEYMAP, -1};
     int i;
     jcalibration = 0;
     jstickenabled = 1;
     for (i = 0; i < NUMJOYKEYS; i++) {
          joykeys[i] = misterjoykeys[i];
     }
}
''', s, count=1, flags=re.S)
JOYBLOCK = '''     if (jstickenabled) {
          // MiSTer: the engine's pad
          const int deadzone = 4096;
          int jvel = 0, jsvel = 0, jangvel = 0;
          if (joynumaxes == 2) {
               jangvel = joyaxis[0];
               jvel = -joyaxis[1];
          }
          else if (joynumaxes >= 4) {
               jangvel = joyaxis[2];
               jvel = -joyaxis[1];
               jsvel = -joyaxis[0];
          }
          if (klabs(jvel) < deadzone) jvel = 0;
          if (klabs(jsvel) < deadzone) jsvel = 0;
          if (klabs(jangvel) < deadzone) jangvel = 0;
          v += 201 * (jvel - ksgn(jvel) * deadzone) / (32767 - deadzone);
          s += 201 * (jsvel - ksgn(jsvel) * deadzone) / (32767 - deadzone);
          a += 112 * (jangvel - ksgn(jangvel) * deadzone) / (32767 - deadzone);

          for (i = 0; i < NUMJOYKEYS; i++) {
               if (joykeys[i] < 0) {
                    continue;                      // a button without an action
               }
               if (((joyb & butbit[i]) == butbit[i])   // button is down
                   &&((oldjoyb & butbit[i]) != butbit[i])) {
                    keystatus[keys[joykeys[i]]] = 1;
                    if (joykeys[i] == KEYRUN) {
                         keystatus[keys[KEYFWD]] = 1;
                    }
               }
               else if (((joyb & butbit[i]) == butbit[i])   // button still down
                        &&((oldjoyb & butbit[i]) == butbit[i])) {
                    if (joykeys[i] == KEYUSE // ..one-time actions
                        || joykeys[i] == KEYJUMP
                        || joykeys[i] == KEYMAP
                        || joykeys[i] == KEYUSEP
                        || joykeys[i] == KEYCAST) {
                         keystatus[keys[joykeys[i]]] = 0;
                    }
               }
               else if (((joyb & butbit[i]) != butbit[i])   // button released
                        &&((oldjoyb & butbit[i]) == butbit[i])) {
                    keystatus[keys[joykeys[i]]] = 0;
                    if (joykeys[i] == KEYRUN) {
                         keystatus[keys[KEYFWD]] = 0;
                    }
               }
          }
          oldjoyb = joyb;
     }
'''
s, n = re.subn(r'     if \(jstickenabled\) \{\n          if \(keystatus\[0x57\].*?\n     \}\n     else if \(jcalibration\) \{.*?\n          oldjoyb = joyb;\n     \}\n', JOYBLOCK, s, count=1, flags=re.S)
assert n == 1 or 'MiSTer: the engine\'s pad' in s, 'joystick block not found'
save('whinp.c', s)

# b5compat.c: the sequel clips permanentwritesprite() to boxes in 320x200
# coordinates (the menu background to 0,0,319,199), rotatesprite's box is in
# screen pixels: scaled, and kept on the screen
s = load('b5compat.c')
s = s.replace('#include "build.h"\n', '#include "build.h"\n#include "pragmas.h"\n', 1)
s = s.replace('''    rotatesprite(thex<<16,they<<16,65536L,0,tilenum,shade,
                 dapalnum,2+8+16+64+128,cx1,cy1,cx2,cy2);''', '''    // the box is in the game's 320x200 coordinates
    cx1 = scale(cx1, xdim, 320); cx2 = scale(cx2 + 1, xdim, 320) - 1;
    cy1 = scale(cy1, ydim, 200); cy2 = scale(cy2 + 1, ydim, 200) - 1;
    if (cx1 < 0) cx1 = 0;
    if (cy1 < 0) cy1 = 0;
    if (cx2 > xdim - 1) cx2 = xdim - 1;
    if (cy2 > ydim - 1) cy2 = ydim - 1;
    rotatesprite(thex<<16,they<<16,65536L,0,tilenum,shade,
                 dapalnum,2+8+16+64+128,cx1,cy1,cx2,cy2);''')
save('b5compat.c', s)


# WH2TRACE markers (temporary) around the new game setup
s = load('whmenu.c')
s = s.replace("""          setupboard(boardname);
          initplayersprite();
          cleanup();""", """          if (getenv("WH2TRACE")) { buildprintf("mark: setupboard %s"NL, boardname); fflush(stdout); }
          setupboard(boardname);
          if (getenv("WH2TRACE")) { buildputs("mark: initplayersprite"NL); fflush(stdout); }
          initplayersprite();
          if (getenv("WH2TRACE")) { buildputs("mark: cleanup"NL); fflush(stdout); }
          cleanup();
          if (getenv("WH2TRACE")) { buildputs("mark: music"NL); fflush(stdout); }""")
s = s.replace('"NL', chr(92) + 'n"')
save('whmenu.c', s)


# whplr.c: the orb arrays have MAXNUMORBS (8) entries; the DOS code wrote a
# ninth (harmless in 1996, undefined behaviour GCC -O2 turns into an endless
# loop that wipes memory: the frozen new game and the audio thread's crash)
s = load('whplr.c')
s = s.replace('if( i < 9 ) {', 'if( i < MAXNUMORBS ) {')
s = s.replace('if (i < 9) {', 'if (i < MAXNUMORBS) {')
save('whplr.c', s)

# mister_port.c (JonoF's Witchaven set, renamed): the menu entry jfSW_WHAVEN2
s = load('mister_port.c')
s = s.replace('(set name jfSW_WHAVEN)', '(set name jfSW_WHAVEN2)')
s = s.replace('#define NO_GAME "Witchaven was not found. Copy everything in the game\'s folder (the one with TILES000.ART, the LEVEL*.MAP files, JOESND and SONGS) to %s/."',
              '#define NO_GAME "Witchaven II was not found. Copy everything in the game\'s folder (the one with TILES000.ART, the LEVEL*.MAP files, JOESND and W_SONGS) to %s/."')
s = s.replace('games[0].id = "WHAVEN";', 'games[0].id = "WHAVEN2";')
s = s.replace('games[0].name = "Witchaven";', 'games[0].name = "Witchaven II";')
save('mister_port.c', s)
# DOS rand() tops out at 32767; glibc's at 2^31-1: the jump-scare face and the
# sparkle effects fired on nearly every frame (the blue skull in every level)
s = load('whfx.c')
s = s.replace('rand() > 32500', '(rand() & 32767) > 32500').replace('rand() > 32700', '(rand() & 32767) > 32700')
save('whfx.c', s)
print('ported (stage 2)')
