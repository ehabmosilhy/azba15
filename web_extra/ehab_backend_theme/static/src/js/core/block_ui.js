/** @odoo-module **/

import { BlockUI } from "@web/core/ui/block_ui";

const { Component, tags, useState } = owl;

BlockUI.template = tags.xml `
    <div t-att-class="state.blockUI ? 'o_blockUI' : ''">
      <t t-if="state.blockUI">
        <div class="o_spinner">
            <svg width="58px" height="58px" xmlns="" viewBox="0 0 100 100"
                 preserveAspectRatio="xMidYMid" class="lds-cube nvd3-svg">
                <g transform="translate(25,25)">
                  <rect ng-attr-x="{{config.dp}}" ng-attr-y="{{config.dp}}"
                        ng-attr-width="{{config.blockSize}}"
                        ng-attr-height="{{config.blockSize}}"
                        ng-attr-fill="{{config.c1}}" x="-18" y="-18"
                        width="36" height="36" fill="#875A7B"
                        transform="scale(1.11648 1.11648)">
                    <animateTransform attributeName="transform" type="scale"
                                      calcMode="spline" values="1.5;1"
                                      keyTimes="0;1" dur="1s"
                                      keySplines="0 0.5 0.5 1" begin="-0.3s"
                                      repeatCount="indefinite"/>
                  </rect>
                </g>
                <g transform="translate(75,25)">
                  <rect ng-attr-x="{{config.dp}}" ng-attr-y="{{config.dp}}"
                        ng-attr-width="{{config.blockSize}}"
                        ng-attr-height="{{config.blockSize}}"
                        ng-attr-fill="{{config.c2}}" x="-18" y="-18"
                        width="36" height="36" fill="#875A7B"
                        transform="scale(1.1619 1.1619)">
                    <animateTransform attributeName="transform" type="scale"
                                      calcMode="spline" values="1.5;1"
                                      keyTimes="0;1" dur="1s"
                                      keySplines="0 0.5 0.5 1" begin="-0.2s"
                                      repeatCount="indefinite"/>
                  </rect>
                </g>
                <g transform="translate(25,75)">
                  <rect ng-attr-x="{{config.dp}}" ng-attr-y="{{config.dp}}"
                        ng-attr-width="{{config.blockSize}}"
                        ng-attr-height="{{config.blockSize}}"
                        ng-attr-fill="{{config.c3}}" x="-18" y="-18"
                        width="36" height="36" fill="#875A7B"
                        transform="scale(1.30165 1.30165)">
                    <animateTransform attributeName="transform" type="scale"
                                      calcMode="spline" values="1.5;1"
                                      keyTimes="0;1" dur="1s"
                                      keySplines="0 0.5 0.5 1" begin="0s"
                                      repeatCount="indefinite"/>
                  </rect>
                </g>
                <g transform="translate(75,75)">
                  <rect ng-attr-x="{{config.dp}}" ng-attr-y="{{config.dp}}"
                        ng-attr-width="{{config.blockSize}}"
                        ng-attr-height="{{config.blockSize}}"
                        ng-attr-fill="{{config.c4}}" x="-18" y="-18"
                        width="36" height="36" fill="#875A7B"
                        transform="scale(1.21853 1.21853)">
                    <animateTransform attributeName="transform" type="scale"
                                      calcMode="spline" values="1.5;1"
                                      keyTimes="0;1" dur="1s"
                                      keySplines="0 0.5 0.5 1" begin="-0.1s"
                                      repeatCount="indefinite"/>
                  </rect>
                </g>
              </svg>
        </div>
        <div class="o_message">
            <t t-raw="state.line1"/> <br/>
            <t t-raw="state.line2"/>
        </div>
      </t>
    </div>`;