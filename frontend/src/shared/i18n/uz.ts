// All customer + admin UI strings live here (Uzbek Latin).
// Adding Russian later = adding one dictionary with the same shape + a locale switch in t().
export const uz = {
  app: {
    title: "Faberlik Sotuv Bot",
    subtitle: "Faberlic konsultanti do'koni",
  },
  openInTelegram: {
    title: "Iltimos, do'konni Telegram orqali oching",
  },
  nav: {
    catalog: "Katalog",
    cart: "Savat",
    orders: "Mening zakazlarim",
  },
  catalog: {
    allCategories: "Hammasi",
    searchPlaceholder: "Nom yoki artikul bo'yicha qidirish",
    empty: "Hech narsa topilmadi",
    emptyCustomLink: "Katalogda yo'q mahsulot uchun forma",
    unavailable: "Mavjud emas",
    addToCart: "Savatga qo'shish",
  },
  product: {
    sku: "Artikul",
    description: "Tavsif",
    back: "Orqaga",
  },
  cart: {
    title: "Savat",
    empty: "Savat bo'sh",
    total: "Jami",
    remove: "O'chirish",
    customPriceLater: "Narx keyin aniqlanadi",
    checkout: "Buyurtma berish",
    addCustom: "Katalogda yo'q mahsulot qo'shish",
    increase: "Ko'paytirish",
    decrease: "Kamaytirish",
    quantityLabel: "Miqdori",
    customItemLabel: "Katalogda yo'q mahsulot",
  },
  customForm: {
    title: "Katalogda yo'q mahsulot",
    name: "Nomi",
    sku: "Artikul",
    photo: "Rasm",
    quantity: "Miqdori",
    note: "Izoh",
    submit: "Savatga qo'shish",
    validationRequired: "Nomi, artikul yoki rasmdan kamida bittasini kiriting",
    uploading: "Yuklanmoqda...",
    photoPreviewAlt: "Yuklangan rasm",
  },
  checkout: {
    title: "Buyurtma rasmiylashtirish",
    name: "Ismingiz",
    nameRequired: "Ismingizni kiriting",
    phone: "Telefon",
    sendContact: "Kontaktni yuborish",
    phoneManualLabel: "Yoki qo'lda kiriting",
    phoneInvalid: "Telefon raqami noto'g'ri",
    delivery: "Yetkazib berish",
    pickup: "Olib ketish",
    address: "Manzil",
    addressRequired: "Manzilni kiriting",
    pickupAddressLabel: "Olib ketish manzili",
    comment: "Izoh (ixtiyoriy)",
    commentTooLong: "Izoh 500 belgidan oshmasligi kerak",
    submit: "Buyurtma berish",
    sending: "Yuborilmoqda...",
  },
  done: {
    title: "Buyurtma qabul qilindi",
    orderNumber: "Buyurtma raqami #{id}",
    backToCatalog: "Katalogga qaytish",
  },
  orders: {
    title: "Mening zakazlarim",
    empty: "Sizda hali buyurtmalar yo'q",
    backToCatalog: "Katalogga qaytish",
    total: "Jami",
  },
  admin: {
    comingSoon: "Admin panel tez orada.",
  },
  errors: {
    invalid_init_data: "Ilova noto'g'ri ochildi. Iltimos, botni qaytadan oching.",
    init_data_expired: "Sessiya muddati tugadi. Iltimos, ilovani qaytadan oching.",
    forbidden: "Ruxsat yo'q",
    not_found: "Topilmadi",
    product_unavailable: "Mahsulot hozircha mavjud emas",
    invalid_transition: "Holatni o'zgartirib bo'lmaydi",
    file_too_large: "Fayl hajmi juda katta (5 MB dan oshmasligi kerak)",
    unsupported_file_type: "Fayl turi qo'llab-quvvatlanmaydi",
    rate_limited: "Juda ko'p urinish, birozdan keyin qayta urinib ko'ring",
    invalid_upload: "Fayl yuklanmadi, qaytadan urinib ko'ring",
    category_not_empty: "Kategoriyada mahsulotlar bor",
    network: "Internet aloqasi yo'q, qaytadan urinib ko'ring",
    generic: "Xatolik yuz berdi, qaytadan urinib ko'ring",
  },
} as const;

type Dict = typeof uz;

function resolve(dict: unknown, path: string[]): unknown {
  let value: unknown = dict;
  for (const part of path) {
    if (value && typeof value === "object" && part in (value as Record<string, unknown>)) {
      value = (value as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return value;
}

/** Looks up `key` (dot path, e.g. "errors.not_found") in the uz dictionary and
 * interpolates `{param}` placeholders. Falls back to the raw key when missing. */
export function t(key: string, params?: Record<string, string | number>): string {
  const value = resolve(uz as Dict, key.split("."));
  let text = typeof value === "string" ? value : key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    }
  }
  return text;
}
