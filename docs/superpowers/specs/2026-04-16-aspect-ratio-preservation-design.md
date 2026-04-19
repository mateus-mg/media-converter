# Design: Correção de Aspect Ratio com Preservação Universal

## Data: 2026-04-16

## Problema

O bug de "amassar" vídeos ocorre quando:
1. Um vídeo é filmado em modo retrato (ex: 9:16) em um celular
2. O ffprobe retorna dimensões brutas em paisagem (ex: 3840x2160)
3. O código detecta rotação=90° mas calcula `is_16_9` ANTES de considerar a rotação
4. 3840/2160 ≈ 16:9 → código força redimensionamento 16:9 exato
5. Resultado: vídeo 9:16 fica distorcido em 16:9

## Solução

### Mudança de Comportamento

**Antes:** Forçar 16:9 exato para vídeos 16:9; usar escala livre para outros.

**Depois:** Preservar aspect ratio original para TODOS os vídeos, apenas escalando para altura alvo.

### Lógica Nova

1. **Detectar rotação primeiro** — obter `rotation` dos metadados
2. **Calcular dimensões efetivas** — se rotação é ±90° ou ±270°, trocar width/height
3. **Calcular aspect ratio efetivo** — usar dimensões já corrigidas
4. **Aplicar escala uniforme** — `scale=-2:{target_height}` para todos os vídeos (preserva aspect ratio)

### Dimensões Efetivas

| Rotação | w brute | h bruto | w efetivo | h efetivo |
|---------|---------|--------|-----------|-----------|
| 0°     | 3840    | 2160   | 3840      | 2160      |
| 90°    | 3840    | 2160   | 2160      | 3840      |
| 180°   | 3840    | 2160   | 3840      | 2160      |
| 270°   | 3840    | 2160   | 2160      | 3840      |

### Resultados por Aspect Ratio

| Aspect Ratio Original | Altura Alvo | Resultado 1080p |
|----------------------|-------------|-----------------|
| 16:9                 | 1080        | 1920x1080       |
| 9:16 (retrato)       | 1080        | 608x1080        |
| 4:3                  | 1080        | 1440x1080       |
| 21:9 (ultrawide)     | 1080        | 1890x1080       |

## Alterações no Código

### 1. Nova função: dimensões efetivas

```python
def get_effective_dimensions(width: int, height: int, rotation: float) -> Tuple[int, int]:
    """Retorna dimensões efetivas considerando rotação."""
    if rotation in (90, -90, 270, -270):
        return height, width
    return width, height
```

### 2. Remover lógica especial 16:9

**Antes (linha 958-969):**
```python
if is_16_9:
    scale_filter = ['-vf', f'scale={target_width}:{target_height}:flags=lanczos']
else:
    scale_filter = ['-vf', f'scale=-2:{target_height}:...']
```

**Depois:**
```python
# Todos os vídeos usam escala uniforme (preserva aspect ratio)
scale_filter = ['-vf', f'scale=-2:{target_height}:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2']
```

### 3. Reordenar detecção de rotação

Mover a detecção de rotação (atualmente linhas 1077-1087) para ANTES do cálculo de scale_filter (linha 947).

### 4. Variável `is_16_9` agora desnecessária

A variável `is_16_9` é usada em:
- Linha 947: cálculo do scale_filter → **REMOVER** (não é mais necessário区分)
- Linha 981: cálculo do preset → **MANTER** (usado para seleção de preset de encoding)

Para o preset, ainda precisamos saber se é 16:9 para otimização de encoder, mas agora usamos dimensões efetivas.

## Arquivos Afetados

- `scripts/media_converter.py`: função `convert_video()`

## Testes Necessários

1. Vídeo 9:16 com rotação=90° → aspect ratio preservado como 9:16
2. Vídeo 16:9 sem rotação → aspect ratio 16:9 preservado
3. Vídeo 4:3 com rotação=180° → aspect ratio 4:3 preservado
4.複 Video 21:9 ultrawide → aspect ratio 21:9 preservado
