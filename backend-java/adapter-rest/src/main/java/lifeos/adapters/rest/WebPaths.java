package lifeos.adapters.rest;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Qué rutas son la web estática ({@code /}, {@code /app}, {@code /app/**}).
 *
 * <p>Se decide sobre el URI crudo, sin decodificar, y falla cerrado: cualquier
 * cosa rara ({@code ..}, {@code %}, {@code ;}, {@code \}, {@code //}, otra
 * capitalización) no cuenta como web y cae en la regla de la API, que exige
 * token. Así ninguna ruta de la API se alcanza sin token por parecer parte
 * de {@code /app}.
 */
final class WebPaths {

    private WebPaths() {}

    static boolean isWeb(HttpServletRequest request) {
        String uri = request.getRequestURI();
        String context = request.getContextPath();
        if (uri == null || !context.isEmpty()) {
            return false;
        }
        if (uri.equals("/") || uri.equals("/app")) {
            return true;
        }
        if (!uri.startsWith("/app/") || uri.contains("//") || uri.indexOf('%') >= 0
                || uri.indexOf(';') >= 0 || uri.indexOf('\\') >= 0) {
            return false;
        }
        for (String segment : uri.split("/")) {
            if (segment.equals(".") || segment.equals("..")) {
                return false;
            }
        }
        return true;
    }
}
