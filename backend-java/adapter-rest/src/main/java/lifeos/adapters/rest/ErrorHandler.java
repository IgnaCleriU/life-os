package lifeos.adapters.rest;

import java.util.Locale;
import java.util.Map;
import lifeos.domain.DomainValidationException;
import lifeos.domain.ProjectNotEmptyException;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.TaskNotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/**
 * Traduce excepciones de dominio y de request a respuestas con la forma uniforme
 * {@code {"error": {"code", "message"}}}, con los mismos códigos que el adapter
 * FastAPI. Los errores que FastAPI no traduce (ruta o método inexistente,
 * restricción de la base, fallo inesperado) usan códigos propios en vez del
 * formato por defecto de Spring, para que todo cliente pueda leer
 * {@code error.code}.
 */
@RestControllerAdvice
class ErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(ErrorHandler.class);

    @ExceptionHandler(DomainValidationException.class)
    ResponseEntity<Map<String, Object>> domainValidation(DomainValidationException e) {
        return error(HttpStatus.BAD_REQUEST, "domain_validation_error", e.getMessage());
    }

    @ExceptionHandler(ProjectNotFoundException.class)
    ResponseEntity<Map<String, Object>> projectNotFound(ProjectNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "project_not_found", e.getMessage());
    }

    @ExceptionHandler(TaskNotFoundException.class)
    ResponseEntity<Map<String, Object>> taskNotFound(TaskNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "task_not_found", e.getMessage());
    }

    @ExceptionHandler(ProjectNotEmptyException.class)
    ResponseEntity<Map<String, Object>> projectNotEmpty(ProjectNotEmptyException e) {
        return error(HttpStatus.CONFLICT, "project_not_empty", e.getMessage());
    }

    /**
     * Body ilegible, path o query con el tipo equivocado, o campo inválido: 422,
     * no el 400 por defecto de Spring, que chocaría con {@code domain_validation_error}.
     */
    @ExceptionHandler({
        RequestValidationException.class,
        HttpMessageNotReadableException.class,
        MethodArgumentTypeMismatchException.class,
        MissingServletRequestParameterException.class,
        HttpMediaTypeNotSupportedException.class,
    })
    ResponseEntity<Map<String, Object>> requestValidation(Exception e) {
        return error(HttpStatus.UNPROCESSABLE_CONTENT, "request_validation_error", e.getMessage());
    }

    /** Una restricción de la base (ej. FK) que los casos de uso no anticiparon. */
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<Map<String, Object>> integrity(DataIntegrityViolationException e) {
        return error(HttpStatus.CONFLICT, "integrity_error", e.getMostSpecificCause().getMessage());
    }

    /**
     * Resto de las excepciones. Las de Spring que ya traen su status (404 de ruta,
     * 405, 406, {@code ResponseStatusException}...) lo conservan, con sus headers
     * (ej. {@code Allow} en el 405) y un código derivado del status:
     * {@code not_found}, {@code method_not_allowed}... Lo demás es un 500 que se
     * loguea y no le filtra el detalle al cliente.
     */
    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, Object>> unexpected(Exception e) {
        if (e instanceof ErrorResponse response) {
            HttpStatusCode status = response.getStatusCode();
            return ResponseEntity.status(status)
                    .headers(response.getHeaders())
                    .body(body(codeFor(status), e.getMessage()));
        }
        log.error("Error inesperado procesando el request", e);
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "internal_error", "Error interno");
    }

    private static String codeFor(HttpStatusCode status) {
        HttpStatus known = HttpStatus.resolve(status.value());
        return known == null
                ? "http_" + status.value()
                : known.name().toLowerCase(Locale.ROOT);
    }

    private static ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(body(code, message));
    }

    private static Map<String, Object> body(String code, String message) {
        return Map.of("error", Map.of("code", code, "message", message == null ? "" : message));
    }
}
