import csv
import pandas as pd
import re
from pathlib import Path

REPO_ROOT = Path(r"c:\Users\USER\Desktop\Claude Cowork Bosmax Agents")
PRODUCT_DIR = REPO_ROOT / "data" / "copywriting_landbank" / "products" / "mwtcb"

# Load angle_bank.csv
angle_df = pd.read_csv(PRODUCT_DIR / "angle_bank.csv")
print(f"Loaded {len(angle_df)} angles.")

hooks = []
subhooks = []
usps = []
ctas = []

def clean_discomfort(text):
    t = str(text).strip()
    if "discomfort" in t.lower():
        if any(w in t.lower() for w in ["dapur", "masak", "kuali"]):
            t = re.sub(r"(?i)\bdiscomfort\b", "sengal-sengal", t)
        elif any(w in t.lower() for w in ["perut", "makan", "pedas", "senak", "mulas", "angin"]):
            t = re.sub(r"(?i)\bdiscomfort\b", "perut rasa tak sedap", t)
        elif any(w in t.lower() for w in ["tidur", "malam", "katil", "bantal"]):
            t = re.sub(r"(?i)\bdiscomfort\b", "tak selesa", t)
        elif any(w in t.lower() for w in ["leher", "tengkuk", "pinggang", "kejang", "lenguh", "sengal"]):
            t = re.sub(r"(?i)\bdiscomfort\b", "sengal-sengal", t)
        else:
            t = re.sub(r"(?i)\bdiscomfort\b", "tak selesa", t)
    return t

def clean_trigger(text):
    t = str(text).strip()
    if not t:
        return ""
    if t[0].isupper() and not t.startswith("POV") and not t.startswith("EDC"):
        t = t[0].lower() + t[1:]
    if t.endswith("."):
        t = t[:-1]
    
    t = clean_discomfort(t)
    
    # Replace other English words if any
    t = t.replace("driver", "pemandu")
    t = t.replace("Driver", "Pemandu")
    t = t.replace("taxi", "teksi")
    t = t.replace("office", "pejabat")
    
    return t

def get_natural_symptom(row):
    text = (str(row['angle_name']) + ' ' + str(row['commercial_trigger']) + ' ' + str(row['hook_direction'])).lower()
    text = text.replace('minyak angin', 'minyak')
    
    # Check for child indicators
    is_child = any(w in text for w in ['bayi', 'anak', 'melalak', 'meragam', 'baby', 'cucu', 'kids', 'budak'])
    # Check for elderly/parent indicators using word boundaries
    is_elderly = bool(re.search(r'\b(sendi|lutut|warga emas|datuk|nenek|tok|makcik|pakcik|mak|ayah|ibu|bapa|orang tua|tua|veteran|parent)\b', text))
    
    if 'selsema' in text or 'selesema' in text or 'bersin' in text:
        return 'selesema anak' if is_child else 'selesema'
    elif 'salah bantal' in text:
        return 'tengkuk kaku salah bantal'
    elif 'tengkuk' in text or 'leher' in text:
        return 'tengkuk kaku lenguh leher'
    elif 'terseliuh' in text or 'kuali' in text or 'tong gas' in text:
        return 'terseliuh ringan'
    elif 'kejang' in text or 'betis' in text or 'simpul biawak' in text:
        return 'lenguh kejang kaki'
    elif 'pinggang' in text:
        return 'lenguh pinggang'
    elif 'tumit' in text or 'pijak lantai' in text:
        return 'tumit kaki rasa tegang'
    elif 'gatal' in text or 'nyamuk' in text or 'serangga' in text:
        return 'gatal-gatal digigit nyamuk'
    elif 'kembung' in text or 'senak' in text or 'ulu hati' in text or 'mulas' in text or 'pedas' in text or 'makan' in text or 'angin' in text or 'perut' in text or 'sebu' in text:
        return 'perut kembung anak' if is_child else 'perut senak berangin'
    elif 'kebas' in text or 'semut' in text:
        return 'kebas-kebas kaki tangan'
    elif is_elderly:
        return 'lenguh sendi orang tua'
    elif 'dapur' in text or 'memasak' in text:
        return 'lenguh sendi bekerja di dapur'
    elif 'pejabat' in text or 'ofis' in text or 'laptop' in text or 'kerja' in text:
        return 'lenguh bahu duduk lama'
    elif 'travel' in text or 'beg' in text or 'kereta' in text or 'glove box' in text or 'jalan' in text or 'sesak' in text or 'jem' in text:
        return 'lenguh badan dalam perjalanan'
    elif 'sukan' in text or 'gym' in text or 'futsal' in text or 'cangkul' in text or 'berkebun' in text or 'lasak' in text:
        return 'sengal-sengal otot selepas bersukan'
    else:
        return 'lenguh-lenguh-badan'

def generate_hook_2(row, trigger_cleaned):
    pb = str(row["primary_bucket"]).upper()
    
    if pb == "STANDBY_BEFORE_NEED":
        return f"POV: Beli siap-siap sebab {trigger_cleaned}."
    elif pb == "FAMILY_HOME":
        return f"Bila {trigger_cleaned}, satu rumah boleh kelam-kabut."
    elif pb == "NOSTALGIA_TRUST":
        return f"Teringat petua arwah tok bila {trigger_cleaned}."
    elif pb == "PRACTICAL_STORAGE":
        return f"POV: Standby sebotol tepi katil kalau {trigger_cleaned}."
    elif pb == "TRAVEL_CAR_BAG":
        return f"Bawa siap-siap dalam beg, senang sapu bila {trigger_cleaned}."
    else:
        return f"POV: Bila {trigger_cleaned}."

def generate_hook_3(row, trigger_cleaned):
    pb = str(row["primary_bucket"]).upper()
    boldness = str(row["boldness_level"]).upper()
    
    if boldness in ["AGGRESSIVE", "BOLD"]:
        if pb == "STANDBY_BEFORE_NEED":
            return f"Jangan tunggu sampai {trigger_cleaned} baru sibuk nak cari minyak!"
        elif pb == "FAMILY_HOME":
            return f"Jangan biar anak bini menanggung siksa sebab {trigger_cleaned}!"
        else:
            return f"Bahaya kalau tak bersedia bila {trigger_cleaned}!"
    else:
        if pb == "NOSTALGIA_TRUST":
            return f"Pernah terfikir tak petua warisan lama untuk redakan {trigger_cleaned}?"
        elif pb == "PRACTICAL_STORAGE":
            return f"Senang cerita, letak satu botol standby sebelum {trigger_cleaned}."
        else:
            return f"Pernah tak korang gelabah bila {trigger_cleaned}?"

def get_usage_context_cue(usage_context, primary_bucket):
    uc = str(usage_context).lower()
    pb = str(primary_bucket).lower()
    if "kitchen" in uc or "dapur" in uc:
        return "dapur"
    elif "car" in uc or "kereta" in uc or "glove" in uc or "dashboard" in uc:
        return "dalam glove box kereta"
    elif "office" in uc or "pejabat" in uc or "it" in uc or "laptop" in uc or "desk" in uc:
        return "atas meja kerja"
    elif "bedroom" in uc or "katil" in uc or "bed" in uc:
        return "tepi katil"
    elif "travel" in uc or "bag" in uc or "beg" in uc:
        return "dalam beg"
    elif "masjid" in uc or "surau" in uc or "mosque" in uc:
        return "dalam poket jubah"
    elif "gym" in uc or "futsal" in uc or "sukan" in uc:
        return "dalam beg sukan"
    elif "emergency" in pb or "standby" in pb:
        return "dalam laci kecemasan rumah"
    else:
        return "dalam laci rumah"

# Loop through all 150 angles
for idx, row in angle_df.iterrows():
    angle_id = row["angle_id"]
    motivation_id = row["motivation_id"]
    primary_bucket = row["primary_bucket"]
    boldness_level = row["boldness_level"]
    buyer_stage = row["buyer_stage"]
    persona_fit = row["persona_fit"]
    usage_context = row["usage_context"]
    sales_mechanism = row["sales_mechanism"]
    platform_surface_fit = row["platform_surface_fit"]
    best_content_format = row["content_format_fit"]
    
    # Get natural symptom mapping
    symptom = get_natural_symptom(row)
    
    # ------------------ HOOKS (3 per angle = 450 hooks) ------------------
    # Hook 1: original hook_direction
    h1_id = f"MWTCB_HOOK_{(idx * 3) + 1:03d}"
    h1_text = clean_discomfort(str(row["hook_direction"]).strip())
    
    # Extract opening pattern
    h1_words = h1_text.split()
    h1_pattern = " ".join(h1_words[:5]) + "..." if len(h1_words) > 5 else h1_text
    
    hooks.append({
        "hook_id": h1_id,
        "product_id": "MWTCB_25ML",
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "hook_text": h1_text,
        "hook_family": str(row["angle_family"]),
        "hook_style": "problem_hook" if "melalak" in h1_text or "sakit" in h1_text.lower() else "nostalgia_hook" if "1958" in h1_text or "kampung" in h1_text else "standby_hook",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "platform_surface_fit": platform_surface_fit,
        "best_content_format": best_content_format,
        "opening_pattern": h1_pattern,
        "emotion_trigger": "panic" if "melalak" in h1_text or "kecemasan" in str(row["angle_name"]).lower() else "nostalgia" if "tok" in h1_text.lower() else "concern",
        "curiosity_gap": "emergency readiness" if "standby" in h1_text.lower() else "remedy speed",
        "visual_prompt_hint": str(row["visual_scene"]),
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "compliance_risk_level": "LOW",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "hook_status": "draft"
    })
    
    # Hook 2: POV style or varied colloquial opening
    h2_id = f"MWTCB_HOOK_{(idx * 3) + 2:03d}"
    trigger_cleaned = clean_trigger(row["commercial_trigger"])
    h2_text = generate_hook_2(row, trigger_cleaned)
    h2_words = h2_text.split()
    h2_pattern = " ".join(h2_words[:5]) + "..." if len(h2_words) > 5 else h2_text
    
    hooks.append({
        "hook_id": h2_id,
        "product_id": "MWTCB_25ML",
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "hook_text": h2_text,
        "hook_family": str(row["angle_family"]),
        "hook_style": "POV_hook",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "platform_surface_fit": platform_surface_fit,
        "best_content_format": best_content_format,
        "opening_pattern": h2_pattern,
        "emotion_trigger": "identification",
        "curiosity_gap": "situation match",
        "visual_prompt_hint": str(row["visual_scene"]),
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "compliance_risk_level": "LOW",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "hook_status": "draft"
    })
    
    # Hook 3: Warning / Question style
    h3_id = f"MWTCB_HOOK_{(idx * 3) + 3:03d}"
    h3_text = generate_hook_3(row, trigger_cleaned)
    h3_words = h3_text.split()
    h3_pattern = " ".join(h3_words[:5]) + "..." if len(h3_words) > 5 else h3_text
    
    hooks.append({
        "hook_id": h3_id,
        "product_id": "MWTCB_25ML",
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "hook_text": h3_text,
        "hook_family": str(row["angle_family"]),
        "hook_style": "warning_hook" if boldness_level in ["AGGRESSIVE", "BOLD"] else "question_hook",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "platform_surface_fit": platform_surface_fit,
        "best_content_format": best_content_format,
        "opening_pattern": h3_pattern,
        "emotion_trigger": "guilt" if boldness_level in ["AGGRESSIVE", "BOLD"] else "empathy",
        "curiosity_gap": "problem solution",
        "visual_prompt_hint": str(row["visual_scene"]),
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "compliance_risk_level": "LOW",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "hook_status": "draft"
    })
    
    # ------------------ SUBHOOKS (3 per angle = 450 subhooks) ------------------
    # Subhook 1: original subhook_direction
    s1_id = f"MWTCB_SUBHOOK_{(idx * 3) + 1:03d}"
    s1_text = clean_discomfort(str(row["subhook_direction"]).strip())
    subhooks.append({
        "subhook_id": s1_id,
        "product_id": "MWTCB_25ML",
        "hook_id": h1_id,
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "subhook_text": s1_text,
        "subhook_role": "standby cue" if "standby" in s1_text.lower() else "situation reason",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "proof_direction": "situation match",
        "visual_support": "show bottle placement in drawer/bag",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "subhook_status": "draft"
    })
    
    # Subhook 2: trust / heritage cue using natural symptom
    s2_id = f"MWTCB_SUBHOOK_{(idx * 3) + 2:03d}"
    s2_text = f"Minyak Cap Burung dengan formula herba asli 1958 untuk melegakan {symptom}."
    subhooks.append({
        "subhook_id": s2_id,
        "product_id": "MWTCB_25ML",
        "hook_id": h2_id,
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "subhook_text": s2_text,
        "subhook_role": "trust cue",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "proof_direction": "heritage proof",
        "visual_support": "close up of retro label",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "subhook_status": "draft"
    })
    
    # Subhook 3: storage / practical cue
    s3_id = f"MWTCB_SUBHOOK_{(idx * 3) + 3:03d}"
    context_cue = get_usage_context_cue(usage_context, primary_bucket)
    s3_text = f"Sebab tu kena standby botol kecil 25ml ni dekat {context_cue}."
    subhooks.append({
        "subhook_id": s3_id,
        "product_id": "MWTCB_25ML",
        "hook_id": h3_id,
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "subhook_text": s3_text,
        "subhook_role": "storage cue",
        "boldness_level": boldness_level,
        "buyer_stage": buyer_stage,
        "persona_fit": persona_fit,
        "primary_bucket": primary_bucket,
        "usage_context": usage_context,
        "sales_mechanism": sales_mechanism,
        "proof_direction": "practical proof",
        "visual_support": "show pocket/glove box fit",
        "source_batch": "2026-06-19_part3_6_copy_components",
        "subhook_status": "draft"
    })

    # ------------------ USPs (200 USPs total) ------------------
    # USP 1: original usp_direction
    u1_id = f"MWTCB_USP_{len(usps) + 1:03d}"
    usp1_text = clean_discomfort(str(row["usp_direction"]).strip())
    usps.append({
        "usp_id": u1_id,
        "product_id": "MWTCB_25ML",
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "usp_text": usp1_text,
        "usp_family": "Sejak 1958" if "1958" in usp1_text else "Minyak hijau tradisi" if "hijau" in usp1_text.lower() else "Botol 25ml",
        "proof_type": "heritage" if "1958" in usp1_text else "product-only visual proof",
        "visual_proof": "show vintage logo" if "1958" in usp1_text else "show green liquid",
        "buyer_reason": "petua warisan dipercayai" if "1958" in usp1_text else "herba pekat tulen",
        "primary_bucket": primary_bucket,
        "usage_context": usage_context,
        "boldness_level": boldness_level,
        "best_content_format": best_content_format,
        "platform_surface_fit": platform_surface_fit,
        "source_batch": "2026-06-19_part3_6_copy_components",
        "usp_status": "draft"
    })
    
    # USP 2: (only for first 50 angles to reach exactly 200 USPs)
    if idx < 50:
        u2_id = f"MWTCB_USP_{len(usps) + 1:03d}"
        if primary_bucket in ["TRAVEL_CAR_BAG", "PRACTICAL_STORAGE"]:
            usp2_text = "Botol kaca hijau 25ml kompak mudah bawa."
            usp2_family = "Compact bottle"
            proof_type = "practical proof"
            visual_proof = "show bag/pocket fit"
            buyer_reason = "mudah bawa ke mana-mana"
        elif primary_bucket in ["NOSTALGIA_TRUST", "FAMILY_HOME"]:
            usp2_text = "Petua turun-temurun sejak 1958 yang dipercayai."
            usp2_family = "Petua turun-temurun"
            proof_type = "heritage"
            visual_proof = "show vintage cabinet context"
            buyer_reason = "khasiat warisan turun-temurun"
        elif primary_bucket in ["VISUAL_RECOGNITION", "TIKTOK_CURIOSITY"]:
            usp2_text = "Identiti botol retro kaca tebal cap merah."
            usp2_family = "Cap merah mudah cam"
            proof_type = "heritage visual cue"
            visual_proof = "close up of red cap"
            buyer_reason = "senang dicari dalam kecemasan"
        else:
            usp2_text = "Sediaan herba asli tradisional untuk standby keluarga."
            usp2_family = "Sesuai standby"
            proof_type = "practical proof"
            visual_proof = "show drawer cabinet placement"
            buyer_reason = "persediaan kecemasan keluarga"
            
        usps.append({
            "usp_id": u2_id,
            "product_id": "MWTCB_25ML",
            "angle_id": angle_id,
            "motivation_id": motivation_id,
            "usp_text": usp2_text,
            "usp_family": usp2_family,
            "proof_type": proof_type,
            "visual_proof": visual_proof,
            "buyer_reason": buyer_reason,
            "primary_bucket": primary_bucket,
            "usage_context": usage_context,
            "boldness_level": boldness_level,
            "best_content_format": best_content_format,
            "platform_surface_fit": platform_surface_fit,
            "source_batch": "2026-06-19_part3_6_copy_components",
            "usp_status": "draft"
        })

    # ------------------ CTAS (1 per angle = 150 CTAs total) ------------------
    c_id = f"MWTCB_CTA_{len(ctas) + 1:03d}"
    cta_text = clean_discomfort(str(row["cta_direction"]).strip())
    
    # Determine family
    if "beg kuning" in cta_text.lower():
        cta_family = "shop_now"
        action_type = "click_beg_kuning"
    elif "standby" in cta_text.lower():
        cta_family = "standby_now"
        action_type = "prepare_stock"
    elif "bundle" in cta_text.lower() or "set" in cta_text.lower():
        cta_family = "bundle_buy"
        action_type = "bundle_checkout"
    else:
        cta_family = "price_check"
        action_type = "view_offer"
        
    ctas.append({
        "cta_id": c_id,
        "product_id": "MWTCB_25ML",
        "angle_id": angle_id,
        "motivation_id": motivation_id,
        "cta_text": cta_text,
        "cta_family": cta_family,
        "buyer_stage": buyer_stage,
        "boldness_level": boldness_level,
        "platform_surface_fit": platform_surface_fit,
        "best_content_format": best_content_format,
        "urgency_level": "HIGH" if "sekarang" in cta_text.lower() or "cepat" in cta_text.lower() else "MEDIUM",
        "action_type": action_type,
        "usage_context": usage_context,
        "source_batch": "2026-06-19_part3_6_copy_components",
        "cta_status": "draft"
    })

print(f"Generated {len(hooks)} hooks (expected 450).")
print(f"Generated {len(subhooks)} subhooks (expected 450).")
print(f"Generated {len(usps)} USPs (expected 200).")
print(f"Generated {len(ctas)} CTAs (expected 150).")

assert len(hooks) == 450, f"Expected 450 hooks, got {len(hooks)}"
assert len(subhooks) == 450, f"Expected 450 subhooks, got {len(subhooks)}"
assert len(usps) == 200, f"Expected 200 USPs, got {len(usps)}"
assert len(ctas) == 150, f"Expected 150 CTAs, got {len(ctas)}"

# Save to canonical location and snapshot normalized location
def write_csv(filename, data, fieldnames):
    canonical_path = PRODUCT_DIR / filename
    snapshot_dir = PRODUCT_DIR / "imports" / "2026-06-19_part3_6_copy_components" / "normalized"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / filename
    
    for p in [canonical_path, snapshot_path]:
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    print(f"Successfully wrote {filename} to canonical and snapshot.")

write_csv("hook_bank.csv", hooks, [
    "hook_id", "product_id", "angle_id", "motivation_id", "hook_text", "hook_family",
    "hook_style", "boldness_level", "buyer_stage", "persona_fit", "primary_bucket",
    "platform_surface_fit", "best_content_format", "opening_pattern", "emotion_trigger",
    "curiosity_gap", "visual_prompt_hint", "usage_context", "sales_mechanism",
    "compliance_risk_level", "source_batch", "hook_status"
])

write_csv("subhook_bank.csv", subhooks, [
    "subhook_id", "product_id", "hook_id", "angle_id", "motivation_id", "subhook_text",
    "subhook_role", "boldness_level", "buyer_stage", "persona_fit", "primary_bucket",
    "usage_context", "sales_mechanism", "proof_direction", "visual_support",
    "source_batch", "subhook_status"
])

write_csv("usp_bank.csv", usps, [
    "usp_id", "product_id", "angle_id", "motivation_id", "usp_text", "usp_family",
    "proof_type", "visual_proof", "buyer_reason", "primary_bucket", "usage_context",
    "boldness_level", "best_content_format", "platform_surface_fit", "source_batch",
    "usp_status"
])

write_csv("cta_bank.csv", ctas, [
    "cta_id", "product_id", "angle_id", "motivation_id", "cta_text", "cta_family",
    "buyer_stage", "boldness_level", "platform_surface_fit", "best_content_format",
    "urgency_level", "action_type", "usage_context", "source_batch", "cta_status"
])
