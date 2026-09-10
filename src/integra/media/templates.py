from __future__ import annotations

from .models import AudioSpec, BrandSpec, MediaManifest, MediaOutputSpec, SceneSpec

_TEMPLATES = {
    "professional_opportunity": {
        "hook": "Tem oportunidade procurando por você",
        "middle": "Conecte-se a novas oportunidades",
        "final": "Conheça o {brand}",
    },
    "service_demand": {
        "hook": "Precisa de {profession}?",
        "middle": "Encontre profissionais para o serviço que você precisa",
        "final": "Encontre no {brand}",
    },
    "business_recruitment": {
        "hook": "Sua empresa precisa de {profession}?",
        "middle": "Aproxime demanda e profissionais disponíveis",
        "final": "Comece pelo {brand}",
    },
}


def available_templates() -> tuple[str, ...]:
    return tuple(_TEMPLATES)


def build_template(
    template_id: str,
    *,
    profession: str,
    brand_name: str = "IntegraTrampo",
    cta: str = "Cadastre-se e receba oportunidades",
) -> MediaManifest:
    if template_id not in _TEMPLATES:
        raise KeyError(f"Template desconhecido: {template_id}")
    tpl = _TEMPLATES[template_id]
    captions = [
        tpl["hook"].format(profession=profession, brand=brand_name),
        tpl["middle"].format(profession=profession, brand=brand_name),
        tpl["final"].format(profession=profession, brand=brand_name),
    ]
    slug = profession.casefold().replace(" ", "-")
    return MediaManifest(
        campaign_id=f"{template_id}-{slug}",
        brand=BrandSpec(name=brand_name, cta=cta, tagline="Conectando pessoas e oportunidades"),
        output=MediaOutputSpec(format="reel", width=1080, height=1920, fps=30, codec="h264"),
        music=AudioSpec(enabled=False),
        voiceover=AudioSpec(enabled=False),
        scenes=[
            SceneSpec(id="scene-01", image=f"assets/{slug}/scene_01.png", duration_seconds=3.2, motion="zoom_in", caption=captions[0]),
            SceneSpec(id="scene-02", image=f"assets/{slug}/scene_02.png", duration_seconds=3.2, motion="pan_left", caption=captions[1]),
            SceneSpec(id="scene-03", image=f"assets/{slug}/scene_03.png", duration_seconds=3.6, motion="zoom_out", caption=captions[2]),
        ],
    )
