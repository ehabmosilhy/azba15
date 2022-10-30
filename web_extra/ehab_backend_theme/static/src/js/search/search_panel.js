odoo.define("ehab_backend_theme.SearchPanel", function(require) {

    const { Model, useModel } = require('web.Model');
    const SearchPanel = require('web.searchPanel');
    const { device } = require("web.config");
    const { hooks } = owl;
    const { useExternalListener, useSubEnv } = hooks;
    const { patch } = require('web.utils');

    patch(SearchPanel.prototype, 'ehab_backend_theme.SearchPanel', {

        setup() {
            useSubEnv({ searchModel: this.props.searchModel });
            this.model = useModel("searchModel");
            this.isMobileView = device.isMobile;
            this._super(...arguments);
        },
        _getCategories() {
            var self = this;
            const categories = this.model.get("sections", s => s.type === "category" && s.activeValueId);
            return _.reduce(_.keys(categories), function(selection, categoryId) {
                var category = categories[categoryId];
                if (category.activeValueId) {
                    selection.push({
                        values: _.map([category.activeValueId].concat(
                            self._getAncestorValueIds(category, category.activeValueId)
                        ), function(valueId) {
                            return category.values.get(valueId).display_name;
                        }),
                        icon: category.icon,
                        color: category.color,
                    });
                }
                return selection;
            }, []);
        },

        _getFilters() {
            const filters = this.model.get("sections", s => s.type === "filter");
            var getCheckedValues = (filter_val) => {
                const filters = [];
                for (const [, value] of filter_val) {
                    value.checked ? filters.push(value.display_name) : false;
                }
                return filters;
            };

            return _.reduce(_.keys(filters), function(selection, filterId) {
                var filter = filters[filterId];
                var values = [];
                if (filter.groups) {
                    values = _.flatten(_.map(_.keys(filter.groups), function(groupId) {
                        return getCheckedValues(filter.groups[groupId].values);
                    }));
                } else if (filter.values) {
                    values = getCheckedValues(filter.values);
                }
                if (!_.isEmpty(values)) {
                    selection.push({
                        values: values,
                        icon: filter.icon,
                        color: filter.color,
                    });
                }
                return selection;
            }, []);
        }
    });
    SearchPanel.props = {
        className: { type: String, optional: 1 },
        importedState: { type: String, optional: 1 },
        searchModel: Model,
    };
});