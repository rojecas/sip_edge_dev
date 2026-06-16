# -*- coding: utf-8 -*-
import pathlib

path = pathlib.Path('harness/specs/09_emergency_mode/requirements.md')
content = path.read_text(encoding='utf-8')

# Check for corruption: if '# Requirements' is not at the start
if not content.startswith('# Requirements'):
    idx = content.find('# Requirements')
    if idx >= 0:
        content = content[idx:]
    else:
        idx = content.find('> Feature 9')
        if idx >= 0:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# Requirements'):
                    content = '\n'.join(lines[i:])
                    break

# R16 old text
old_r16 = 'SI el sistema recibe un SMS entrante cuyo texto no coincide con ning' + '\u00fan' + ' comando\n'
old_r16 += 'v' + '\u00e1' + 'lido (manual on, manual on Xh/Xm, manual on EXT Xh/Xm, manual off)\n'
old_r16 += 'ENTONCES el sistema DEBE ignorar el comando, no modificar el estado del modo\n'
old_r16 += 'manual y registrar el evento en emergency_mode_log con status = ' + "'invalid'" + '\n'
old_r16 += 'y el texto crudo recibido.'

new_r16 = 'SI el sistema recibe un SMS entrante cuyo texto no coincide con ning' + '\u00fan' + ' comando\n'
new_r16 += 'v' + '\u00e1' + 'lido (manual on, manual on Xh/Xm, manual on EXT Xh/Xm, manual off)\n'
new_r16 += 'ENTONCES el sistema DEBE:\n'
new_r16 += '- Ignorar el comando y no modificar el estado del modo manual.\n'
new_r16 += '- Registrar el evento en emergency_mode_log con status = ' + "'invalid'" + ' y el texto crudo recibido.\n'
new_r16 += '- Responder al remitente con un SMS que indique que el comando no es v' + '\u00e1' + 'lido y\n'
new_r16 += '  muestre la lista de comandos aceptados: manual on, manual on Xh/Xm,\n'
new_r16 += '  manual on EXT Xh/Xm, manual off.'

if old_r16 in content:
    content = content.replace(old_r16, new_r16)
    print('R16 OK')
else:
    # Try alt version without backticks
    alt = 'SI el sistema recibe un SMS entrante cuyo texto no coincide con ning' + '\u00fan' + ' comando\n'
    alt += 'v' + '\u00e1' + 'lido (manual on, manual on Xh/Xm, manual on EXT Xh/Xm, manual off)\n'
    alt += 'ENTONCES el sistema DEBE:\n'
    alt += '- Ignorar el comando y no modificar el estado del modo manual.\n'
    alt += '- Registrar el evento en emergency_mode_log con status = ' + "'invalid'" + ' y el texto crudo recibido.\n'
    alt += '- Responder al remitente con un SMS que indique que el comando no es v' + '\u00e1' + 'lido y\n'
    alt += '  muestre la lista de comandos aceptados: manual on, manual on Xh/Xm,\n'
    alt += '  manual on EXT Xh/Xm, manual off.'
    if alt in content:
        content = content.replace(alt, new_r16)
        print('R16 OK (alt)')
    else:
        print('R16 NOT FOUND!')

# R17 old text
old_r17 = 'CUANDO el sistema recibe un comando SMS de tipo manual on, manual on EXT X\n'
old_r17 += 'o manual off, DEBE verificar que el n' + '\u00fa' + 'mero de tel' + '\u00e9' + 'fono emisor corresponda a\n'
old_r17 += 'un usuario con rol dmin registrado en la tabla users. SI el emisor no es\n'
old_r17 += 'un administrador, el sistema DEBE ignorar el comando y registrarlo como no\n'
old_r17 += 'autorizado en emergency_mode_log.'

new_r17 = 'CUANDO el sistema recibe un comando SMS de tipo manual on, manual on EXT X\n'
new_r17 += 'o manual off, DEBE verificar que el n' + '\u00fa' + 'mero de tel' + '\u00e9' + 'fono emisor corresponda a\n'
new_r17 += 'un usuario con rol dmin registrado en la tabla users. SI el emisor no es\n'
new_r17 += 'un administrador, el sistema DEBE:\n'
new_r17 += '- Ignorar el comando.\n'
new_r17 += '- Registrarlo como no autorizado en emergency_mode_log.\n'
new_r17 += '- Responder al remitente con un SMS informando que los comandos de modo manual\n'
new_r17 += "  s" + '\u00f3' + "lo se aceptan desde n" + '\u00fa' + "meros de tel" + '\u00e9' + "fono registrados de administradores."

if old_r17 in content:
    content = content.replace(old_r17, new_r17)
    print('R17 OK')
else:
    # Find close match
    idx = content.find('CUANDO el sistema recibe un comando SMS')
    if idx >= 0:
        print('R17 area found at', idx)
        print('First 150 chars:', content[idx:idx+150])
    print('R17 NOT FOUND!')

# R19 old text
old_r19 = 'SI el modo manual no est' + '\u00e1' + ' activo Y el sistema recibe un comando manual on EXT\n'
old_r19 += 'Xh/Xm, ENTONCES el sistema DEBE ignorar el comando y registrarlo como\n'
old_r19 += 'invalid en emergency_mode_log.'

new_r19 = 'SI el modo manual no est' + '\u00e1' + ' activo Y el sistema recibe un comando manual on EXT\n'
new_r19 += 'Xh/Xm, ENTONCES el sistema DEBE:\n'
new_r19 += '- Ignorar el comando y registrarlo como invalid en emergency_mode_log.\n'
new_r19 += '- Responder al remitente con un SMS informando que el modo manual no est' + '\u00e1' + '\n'
new_r19 += '  activo y que el comando correcto para activarlo es manual on o\n'
new_r19 += '  manual on Xh/Xm.'

if old_r19 in content:
    content = content.replace(old_r19, new_r19)
    print('R19 OK')
else:
    idx = content.find('SI el modo manual no est')
    if idx >= 0:
        print('R19 area found at', idx)
        print('First 200 chars:', content[idx:idx+200])
    print('R19 NOT FOUND!')

path.write_text(content, encoding='utf-8')
print('Done')
