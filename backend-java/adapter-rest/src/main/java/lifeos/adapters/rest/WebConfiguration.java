package lifeos.adapters.rest;

import java.beans.PropertyEditorSupport;
import java.util.UUID;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.InitBinder;

/** Ajustes del binding de Spring MVC para igualar la validación del adapter FastAPI. */
@ControllerAdvice
class WebConfiguration {

    /**
     * Path variables {@code UUID} solo en forma canónica. El binding por defecto
     * usa {@link UUID#fromString}, que acepta ids mal formados como
     * {@code 1-1-1-1-1} y los convertiría en 404 en vez de 422. Va como editor y
     * no como converter porque los editores tienen prioridad en el binder.
     */
    @InitBinder
    void strictUuids(WebDataBinder binder) {
        binder.registerCustomEditor(UUID.class, new PropertyEditorSupport() {
            @Override
            public void setAsText(String text) {
                setValue(RequestParsing.canonicalUuid(text));
            }
        });
    }
}
