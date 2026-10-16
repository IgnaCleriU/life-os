package lifeos.adapters.rest;

import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * {@code GET /app/}: el {@code index.html}. El resto de {@code /app/**} lo
 * resuelve {@link WebAppConfiguration}; Spring no manda la ruta vacía al
 * handler de recursos, por eso esta va aparte.
 */
@RestController
class WebAppController {

    private static final Resource INDEX = new ClassPathResource("static/app/index.html");

    @GetMapping("/app/")
    ResponseEntity<Resource> index() {
        if (!INDEX.exists()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok()
                .cacheControl(CacheControl.noCache())
                .contentType(MediaType.TEXT_HTML)
                .body(INDEX);
    }
}
