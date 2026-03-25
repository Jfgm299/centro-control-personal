# Module Registry

| Module | Schema | Status | Has Automation Contract |
|--------|--------|--------|------------------------|
| `gym_tracker` | `gym_tracker` | ✅ Production | ❌ |
| `expenses_tracker` | `expenses_tracker` | ✅ Production | ✅ |
| `macro_tracker` | `macro_tracker` | ✅ Production | ❌ |
| `flights_tracker` | `flights_tracker` | ✅ Production | ✅ |
| `travels_tracker` | `travels_tracker` | ✅ Production | ❌ |
| `calendar_tracker` | `calendar_tracker` | ✅ Production | ✅ (reference implementation) |
| `automations_engine` | `automations` | ✅ Production | N/A (es el motor) |

## Notes

- **calendar_tracker** es la implementación de referencia del automation contract. Ver `calendar_tracker.md` para los detalles completos.
- **travels_tracker** usa **Cloudflare R2** para almacenamiento de fotos — no AWS S3. boto3 apunta al endpoint de R2.
- **flights_tracker** usa **AeroDataBox API** (vía RapidAPI) para datos de vuelos.
- **macro_tracker** usa **Open Food Facts API** para búsqueda de alimentos.
- **automations_engine** no es un módulo de dominio — es la infraestructura que ejecuta los flujos de automatización.
