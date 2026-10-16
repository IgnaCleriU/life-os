package lifeos.adapters.rest;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** Healthcheck del backend: valida que la app está viva. */
@RestController
class HealthController {

    @GetMapping("/health")
    Map<String, String> health() {
        return Map.of("status", "ok");
    }
}
